"""Local-only Tk editor for model-specific estimated token prices."""
import json
import math
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
from meter_client import request, summary
from usage_meter import OPENAI_PRICES

ROOT = Path(__file__).resolve().parents[1]
RATE_FILE = ROOT / 'private' / 'token_rates.json'
FIELDS = (('input', '未缓存输入'), ('cached_input', '缓存输入'),
          ('output', '输出（含推理 Token）'), ('cache_write', '缓存写入（可留空）'))


class RateEditor:
    def __init__(self, root):
        self.root = root
        root.title('Codex Companion · Token 费率')
        root.geometry('950x900')
        root.minsize(800, 680)
        self.currency = tk.StringVar(value='USD')
        self.model = tk.StringVar()
        self.model_override = tk.StringVar()
        self.rate_source = tk.StringVar(value='custom')
        self.multiplier = tk.StringVar(value='1')
        self.previous_source = 'custom'
        self.custom_backup = {}
        self.values = {key: tk.StringVar() for key, _ in FIELDS}
        self.long_enabled = tk.BooleanVar()
        self.long_threshold = tk.StringVar(value='272000')
        self.long_values = {key: tk.StringVar() for key, _ in FIELDS}
        self.base_entries = {}
        self.long_entries = {}
        self.status = tk.StringVar(value='按每 1,000,000 Token 填写；默认不估价。')
        self.rates = {}
        self._layout()
        self._read()
        self._refresh()

    def _layout(self):
        outer = ttk.Frame(self.root, padding=16); outer.pack(fill='both', expand=True)
        left = ttk.Frame(outer, width=235); left.pack(side='left', fill='y', padx=(0, 16)); left.pack_propagate(False)
        ttk.Label(left, text='已配置模型', font=('', 14, 'bold')).pack(anchor='w', pady=(0, 8))
        self.models = tk.Listbox(left, exportselection=False); self.models.pack(fill='both', expand=True)
        self.models.bind('<<ListboxSelect>>', self._select)
        ttk.Button(left, text='删除所选模型费率', command=self._delete).pack(fill='x', pady=(8, 0))
        right = ttk.Frame(outer); right.pack(side='left', fill='both', expand=True)
        ttk.Label(right, text='模型与价格（USD $）', font=('', 14, 'bold')).grid(row=0, column=0, sticky='w', pady=(0, 8))
        ttk.Label(right, text='模型 ID').grid(row=1, column=0, sticky='w', pady=5)
        ttk.Entry(right, textvariable=self.model).grid(row=1, column=1, sticky='ew', pady=5)
        ttk.Label(right, text='设备模型校准（可选）').grid(row=2, column=0, sticky='w', pady=5)
        ttk.Entry(right, textvariable=self.model_override).grid(row=2, column=1, sticky='ew', pady=5)
        ttk.Label(right, text='留空自动监听 App Server；手动填写仅校准显示及估价模型，不会切换 Codex。', foreground='#666', wraplength=430).grid(row=3, column=0, columnspan=2, sticky='w')
        ttk.Label(right,text='价格来源').grid(row=4,column=0,sticky='w',pady=(12,4))
        self.source_box=ttk.Combobox(right,textvariable=self.rate_source,state='readonly',values=('custom','openai'),width=24)
        self.source_box.grid(row=4,column=1,sticky='w',pady=(12,4));self.source_box.bind('<<ComboboxSelected>>',self._source_changed)
        ttk.Label(right,text='倍率（默认 1）').grid(row=5,column=0,sticky='w',pady=4)
        ttk.Entry(right,textvariable=self.multiplier,width=18).grid(row=5,column=1,sticky='w',pady=4)
        ttk.Label(right, text='基准价 / 1,000,000 Token', font=('', 14, 'bold')).grid(row=6, column=0, sticky='w', pady=(8, 4))
        for row, (key, label) in enumerate(FIELDS, 7):
            ttk.Label(right, text=label).grid(row=row, column=0, sticky='w', pady=5)
            price=ttk.Frame(right);price.grid(row=row,column=1,sticky='w',pady=5)
            ttk.Label(price,text='$').pack(side='left',padx=(0,4))
            entry=ttk.Entry(price, textvariable=self.values[key], width=18);entry.pack(side='left');self.base_entries[key]=entry
        tier=ttk.LabelFrame(right,text='长上下文分档（单次输入含缓存，严格超过阈值）',padding=8)
        tier.grid(row=11,column=0,columnspan=2,sticky='ew',pady=8)
        ttk.Checkbutton(tier,text='启用长档',variable=self.long_enabled).grid(row=0,column=0,sticky='w')
        ttk.Entry(tier,textvariable=self.long_threshold,width=16).grid(row=0,column=1,sticky='w')
        for row,(key,label) in enumerate(FIELDS,1):
            ttk.Label(tier,text=label+' $ / 1M').grid(row=row,column=0,sticky='w')
            entry=ttk.Entry(tier,textvariable=self.long_values[key],width=16);entry.grid(row=row,column=1,sticky='w');self.long_entries[key]=entry
        note = ('OpenAI 模式采用当前公开单价，仅核对过的模型可选；custom 模式由你填写基准价。\n'
                '两种模式都乘倍率一次；默认倍率为 1。推理单独显示，费率同输出且合计不重复。\n'
                '长档按完整单次请求判档；缺少旧请求边界时不猜。费率只保存在本机。')
        ttk.Label(right, text=note, justify='left', foreground='#666').grid(row=16, column=0, columnspan=2, sticky='w', pady=(12, 8))
        buttons=ttk.Frame(right);buttons.grid(row=17,column=0,columnspan=2,sticky='w')
        ttk.Button(buttons, text='保存费率', command=self._save).pack(side='left')
        ttk.Button(buttons, text='保存模型校准', command=self._save_override).pack(side='left',padx=8)
        ttk.Button(buttons, text='检查当前计量', command=self._diagnose).pack(side='left')
        ttk.Button(right,text='清零控制器计数',command=self._clear).grid(row=19,column=0,columnspan=2,sticky='w',pady=8)
        ttk.Label(right, textvariable=self.status, wraplength=520, foreground='#555').grid(row=18, column=0, columnspan=2, sticky='w', pady=(10, 0))
        right.columnconfigure(1, weight=1)

    def _read(self):
        try:
            data = json.loads(RATE_FILE.read_text())
            self.currency.set('USD')
            self.rates = data.get('models') if isinstance(data.get('models'), dict) else {}
        except (OSError, ValueError, TypeError):
            self.rates = {}
        try:
            override=json.loads((ROOT/'private'/'model_override.json').read_text())
            if isinstance(override,dict):self.model_override.set(str(override.get('model_id','')))
        except (OSError,ValueError,TypeError):pass

    def _diagnose(self):
        try:messagebox.showinfo('当前 Token 计量',summary(request({'type':'status'})))
        except (OSError,ValueError) as error:messagebox.showerror('Bridge 未连接',str(error))

    def _clear(self):
        try:
            status=request({'type':'status'});meter=status.get('metering')
            if not meter:raise ValueError('运行中的 Bridge 尚未更新。')
            if not messagebox.askyesno('清零控制器计数','仅清零控制器累计 Token 与估价。聊天和账单不变。继续吗？'):return
            result=request({'type':'meter_reset','meter_id':meter['usage']['meter_id']})
            if not result.get('cleared'):raise ValueError('状态已变化或保存失败，请重新检查。')
            self.status.set('计数已清零，设备下次同步时更新。')
        except (OSError,ValueError) as error:messagebox.showerror('未能清零',str(error))

    def _save_override(self):
        model=self.model_override.get().strip()
        if len(model)>96:messagebox.showerror('检查输入','模型 ID 最长 96 个字符。');return
        path=ROOT/'private'/'model_override.json'
        try:
            path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            temp=path.with_suffix('.json.tmp');temp.write_text(json.dumps({'model_id':model},ensure_ascii=False)+'\n',encoding='utf-8')
            os.chmod(temp,0o600);temp.replace(path);os.chmod(path,0o600)
            self.status.set('已保存模型校准；Bridge 下次同步时生效。留空即恢复自动监听。')
        except OSError as error:self.status.set(f'保存失败：{error}')

    def _refresh(self):
        self.models.delete(0, tk.END)
        for model in sorted(self.rates): self.models.insert(tk.END, model)

    def _select(self, _event=None):
        selected = self.models.curselection()
        if not selected: return
        key = self.models.get(selected[0]); row = self.rates.get(key, {})
        self.model.set(key)
        self.rate_source.set(row.get('rate_source','custom'))
        self.previous_source=self.rate_source.get()
        self.multiplier.set(str(row.get('multiplier',1)))
        base=row.get('custom_prices',row)
        self.custom_backup={field:base.get(field) for field,_ in FIELDS}
        self.custom_backup['long_context']=base.get('long_context',{})
        for field, _ in FIELDS: self.values[field].set('' if base.get(field) is None else str(base[field]))
        base_long=base.get('long_context',{})
        self.long_enabled.set(bool(base_long));self.long_threshold.set(str(base_long.get('above_input_tokens',272000)))
        for field,_ in FIELDS:self.long_values[field].set('' if base_long.get(field) is None else str(base_long[field]))
        self._source_changed()

    def _source_changed(self, _event=None):
        mode=self.rate_source.get()
        entries=tuple(self.base_entries.values())+tuple(self.long_entries.values())
        if mode=='openai' and self.previous_source=='custom':
            self.custom_backup={field:(self.values[field].get() or None) for field,_ in FIELDS}
            self.custom_backup['long_context']={'above_input_tokens':int(self.long_threshold.get() or 272000),
                **{field:(self.long_values[field].get() or None) for field,_ in FIELDS}}
        elif mode=='custom' and self.previous_source=='openai' and self.custom_backup:
            for field,_ in FIELDS:self.values[field].set('' if self.custom_backup.get(field) is None else str(self.custom_backup[field]))
            old=self.custom_backup.get('long_context',{})
            self.long_enabled.set(bool(old));self.long_threshold.set(str(old.get('above_input_tokens',272000)))
            for field,_ in FIELDS:self.long_values[field].set('' if old.get(field) is None else str(old[field]))
        self.previous_source=mode
        if mode=='openai':
            card=OPENAI_PRICES.get(self.model.get().strip())
            if not card:
                self.status.set('此模型没有内置 OpenAI 官方价格卡；请切回 custom 手动填写。')
                for entry in entries: entry.state(['disabled'])
                return
            for key,_ in FIELDS:self.values[key].set('' if card.get(key) is None else str(card[key]))
            long=card.get('long_context',{})
            self.long_enabled.set(bool(long));self.long_threshold.set(str(long.get('above_input_tokens',272000)))
            for key,_ in FIELDS:self.long_values[key].set('' if long.get(key) is None else str(long[key]))
            for entry in entries: entry.state(['disabled'])
            self.status.set('已加载 OpenAI 官方价格；倍率会单独应用一次。')
        else:
            for entry in entries: entry.state(['!disabled'])
            self.status.set('custom：基准价 × 倍率；倍率默认 1。')

    def _save_file(self):
        RATE_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        data = json.dumps({'currency': self.currency.get().strip().upper(), 'models': self.rates}, ensure_ascii=False, indent=2) + '\n'
        temp = RATE_FILE.with_suffix('.json.tmp')
        temp.write_text(data, encoding='utf-8'); os.chmod(temp, 0o600); temp.replace(RATE_FILE); os.chmod(RATE_FILE, 0o600)

    def _save(self):
        model = self.model.get().strip()
        if not model or len(model) > 96:
            messagebox.showerror('检查输入', '请输入有效的模型 ID。'); return
        try: multiplier=float(self.multiplier.get())
        except ValueError: messagebox.showerror('检查输入','倍率需要是非负数字。'); return
        if not math.isfinite(multiplier) or multiplier < 0 or multiplier > 1_000_000:
            messagebox.showerror('检查输入','倍率超出允许范围。'); return
        source=self.rate_source.get()
        if source=='openai' and model not in OPENAI_PRICES:
            messagebox.showerror('没有官方价格卡','请切回 custom 并填写该模型价格。'); return
        row = {'rate_source': source, 'multiplier': multiplier}
        custom = {}
        for key, label in FIELDS:
            raw = self.values[key].get().strip()
            if key == 'cache_write' and not raw: row[key] = None; continue
            try: value = float(raw)
            except ValueError: messagebox.showerror('检查输入', f'{label}需要是非负数字。'); return
            if not math.isfinite(value) or value < 0 or value > 1_000_000:
                messagebox.showerror('检查输入', f'{label}超出允许范围。'); return
            row[key] = value
            custom[key] = value
        if self.long_enabled.get():
            try:
                threshold=int(self.long_threshold.get())
                if not 0<threshold<=10**12:raise ValueError('阈值必须为正整数')
                long={}
                for key,label in FIELDS:
                    raw=self.long_values[key].get().strip()
                    price=None if key=='cache_write' and not raw else float(raw)
                    if price is not None and (not math.isfinite(price) or not 0<=price<=1000000):raise ValueError('长档价格无效')
                    long[key]=price
                row['long_context']=dict(long,above_input_tokens=threshold)
                custom['long_context']=dict(long,above_input_tokens=threshold)
            except ValueError:
                messagebox.showerror('检查输入','请填写有效的长档阈值及折后每百万 Token 价格。');return
        if source=='openai':
            old=self.rates.get(model,{})
            if isinstance(old.get('custom_prices'),dict):row['custom_prices']=old['custom_prices']
            elif self.custom_backup:row['custom_prices']=self.custom_backup
        else:
            row['custom_prices']=custom
        self.rates[model] = row
        try:
            self._save_file(); self.currency.set('USD'); self._refresh()
            self.status.set('已保存到本机私有费率文件；Bridge 下次同步时生效。')
        except OSError as error: self.status.set(f'保存失败：{error}')

    def _delete(self):
        selected = self.models.curselection()
        if not selected: return
        key = self.models.get(selected[0]); self.rates.pop(key, None)
        try:
            self._save_file(); self._refresh(); self.status.set(f'已删除 {key} 的费率。')
            if self.model.get() == key: self.model.set(''); [value.set('') for value in self.values.values()]
        except OSError as error: self.status.set(f'保存失败：{error}')


if __name__ == '__main__':
    window = tk.Tk(); RateEditor(window); window.mainloop()
