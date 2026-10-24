"""Local-only Tk editor for model-specific estimated token prices."""
import json
import math
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

ROOT = Path(__file__).resolve().parents[1]
RATE_FILE = ROOT / 'private' / 'token_rates.json'
FIELDS = (('input', '未缓存输入'), ('cached_input', '缓存输入'),
          ('output', '输出（含推理 Token）'), ('cache_write', '缓存写入（可留空）'))


class RateEditor:
    def __init__(self, root):
        self.root = root
        root.title('Codex Companion · Token 费率')
        root.geometry('760x490')
        root.minsize(690, 430)
        self.currency = tk.StringVar(value='USD')
        self.model = tk.StringVar()
        self.model_override = tk.StringVar()
        self.values = {key: tk.StringVar() for key, _ in FIELDS}
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
        ttk.Label(right, text='美元 / 1,000,000 Token', font=('', 14, 'bold')).grid(row=4, column=0, sticky='w', pady=(18, 8))
        for row, (key, label) in enumerate(FIELDS, 5):
            ttk.Label(right, text=label).grid(row=row, column=0, sticky='w', pady=5)
            price=ttk.Frame(right);price.grid(row=row,column=1,sticky='w',pady=5)
            ttk.Label(price,text='$').pack(side='left',padx=(0,4))
            ttk.Entry(price, textvariable=self.values[key], width=18).pack(side='left')
        note = ('费用按本地费率估算。推理 Token 已包含在输出 Token 中，不重复计费。\n'
                '若出现缓存写入但没有设置对应费率，将不显示费用合计。\n'
                '本窗口只在本机保存费率，不读取账户凭据或 API 密钥。')
        ttk.Label(right, text=note, justify='left', foreground='#666').grid(row=10, column=0, columnspan=2, sticky='w', pady=(12, 8))
        buttons=ttk.Frame(right);buttons.grid(row=11,column=0,columnspan=2,sticky='w')
        ttk.Button(buttons, text='保存费率', command=self._save).pack(side='left')
        ttk.Button(buttons, text='保存模型校准', command=self._save_override).pack(side='left',padx=8)
        ttk.Label(right, textvariable=self.status, wraplength=440, foreground='#555').grid(row=12, column=0, columnspan=2, sticky='w', pady=(10, 0))
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
        for field, _ in FIELDS: self.values[field].set('' if row.get(field) is None else str(row[field]))

    def _save_file(self):
        RATE_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        data = json.dumps({'currency': self.currency.get().strip().upper(), 'models': self.rates}, ensure_ascii=False, indent=2) + '\n'
        temp = RATE_FILE.with_suffix('.json.tmp')
        temp.write_text(data, encoding='utf-8'); os.chmod(temp, 0o600); temp.replace(RATE_FILE); os.chmod(RATE_FILE, 0o600)

    def _save(self):
        model = self.model.get().strip()
        if not model or len(model) > 96:
            messagebox.showerror('检查输入', '请输入有效的模型 ID。'); return
        row = {}
        for key, label in FIELDS:
            raw = self.values[key].get().strip()
            if key == 'cache_write' and not raw: row[key] = None; continue
            try: value = float(raw)
            except ValueError: messagebox.showerror('检查输入', f'{label}需要是非负数字。'); return
            if not math.isfinite(value) or value < 0 or value > 1_000_000:
                messagebox.showerror('检查输入', f'{label}超出允许范围。'); return
            row[key] = value
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
