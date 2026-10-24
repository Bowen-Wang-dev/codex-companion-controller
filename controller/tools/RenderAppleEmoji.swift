import AppKit
let destination=CommandLine.arguments[1]
try FileManager.default.createDirectory(atPath: destination, withIntermediateDirectories: true)
let glyphs=["idle":"😋","working":"🤔","permission":"🥺","delight":"😆","crying":"😭","completed":"🥳","neutral":"😐","palms":"🤲"]
for (name,glyph) in glyphs {
 let size=128
 let bitmap=NSBitmapImageRep(bitmapDataPlanes:nil,pixelsWide:size,pixelsHigh:size,bitsPerSample:8,samplesPerPixel:4,hasAlpha:true,isPlanar:false,colorSpaceName:.deviceRGB,bytesPerRow:size*4,bitsPerPixel:32)!
 let context=NSGraphicsContext(bitmapImageRep:bitmap)!
 NSGraphicsContext.saveGraphicsState(); NSGraphicsContext.current=context
 context.cgContext.clear(CGRect(x:0,y:0,width:size,height:size))
 let attrs:[NSAttributedString.Key:Any]=[.font:NSFont(name:"Apple Color Emoji",size:112)!]
 let string=glyph as NSString; let bounds=string.size(withAttributes:attrs)
 string.draw(at:NSPoint(x:(128-bounds.width)/2,y:(128-bounds.height)/2),withAttributes:attrs)
 NSGraphicsContext.restoreGraphicsState()
 try bitmap.representation(using:.png,properties:[:])!.write(to:URL(fileURLWithPath:destination+"/"+name+".png"))
}
