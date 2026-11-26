# Driver minimo SSD1306 128x64 por I2C (sin dependencias externas)
import framebuf

class SSD1306(framebuf.FrameBuffer):
    def __init__(self, i2c, addr=0x3C, w=128, h=64):
        self.i2c, self.addr, self.width, self.height = i2c, addr, w, h
        self.pages = h // 8
        self.buf = bytearray(self.pages * w)
        super().__init__(self.buf, w, h, framebuf.MONO_VLSB)
        for c in (0xAE, 0x20, 0x00, 0x40, 0xA1, 0xA8, h - 1, 0xC8, 0xD3, 0x00,
                  0xDA, 0x12, 0xD5, 0x80, 0xD9, 0xF1, 0xDB, 0x30, 0x81, 0xFF,
                  0xA4, 0xA6, 0x8D, 0x14, 0xAF):
            self.cmd(c)
        self.fill(0)
        self.show()

    def cmd(self, c):
        self.i2c.writeto(self.addr, bytes([0x80, c]))

    def show(self):
        for c in (0x21, 0, self.width - 1, 0x22, 0, self.pages - 1):
            self.cmd(c)
        self.i2c.writeto(self.addr, b"\x40" + self.buf)
