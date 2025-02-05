ADDR = 0x29
INTG_TIME_MS = 511.2


REG_CMD = 0b10000000
REG_CMD_AUTO_INC = 0b00100000
REG_CLEAR_L = REG_CMD | REG_CMD_AUTO_INC | 0x14
REG_RED_L = REG_CMD | REG_CMD_AUTO_INC | 0x16
REG_GREEN_L = REG_CMD | REG_CMD_AUTO_INC | 0x18
REG_BLUE_L = REG_CMD | REG_CMD_AUTO_INC | 0x1A

REG_ENABLE = REG_CMD | 0
REG_ATIME = REG_CMD | 1
REG_CONTROL = REG_CMD | 0x0f
REG_STATUS = REG_CMD | 0x13

REG_CONTROL_GAIN_1X = 0b00000000
REG_CONTROL_GAIN_4X = 0b00000001
REG_CONTROL_GAIN_16X = 0b00000010
REG_CONTROL_GAIN_60X = 0b00000011

REG_ENABLE_INTERRUPT = 1 << 4
REG_ENABLE_WAIT = 1 << 3
REG_ENABLE_RGBC = 1 << 1
REG_ENABLE_POWER = 1

CH_RED = 0
CH_GREEN = 1
CH_BLUE = 2
CH_CLEAR = 3

TCS_GA = 1.0
TCS_DF = 310
TCS_R_COEF = 0.136
TCS_G_COEF = 1.000
TCS_B_COEF = -0.444
TCS_C_COEF = 3810
TCS_C_OFFSET = 1391



class tcs3472:
    def __init__(self, i2c_bus=None, addr=ADDR):
        self._is_setup = False
        self.addr = addr
        self.i2c_bus = i2c_bus
        if not hasattr(i2c_bus, "read_word_data") or not hasattr(i2c_bus, "write_byte_data"):
            raise TypeError("Object given for i2c_bus must implement read_word_data and write_byte_data")
        self.get_gain()

    def setup(self):
        if self._is_setup:
            return

        self._is_setup = True

        self.i2c_bus.write_byte_data(ADDR, REG_ENABLE, REG_ENABLE_RGBC | REG_ENABLE_POWER)
        self.set_integration_time_ms(INTG_TIME_MS)

    def set_integration_time_ms(self, ms):
        """Set the sensor integration time in milliseconds.

        :param ms: The integration time in milliseconds from 2.4 to 612, in increments of 2.4.

        """
        if ms < 2.4 or ms > 612:
            raise TypeError("Integration time must be between 2.4 and 612ms")
        self._atime = int(round(ms / 2.4))
        self._max_count = min(65535, (256 - self._atime) * 1024)

        self.setup()

        self.i2c_bus.write_byte_data(ADDR, REG_ATIME, 256 - self._atime)

    def max_count(self):
        """Return the maximum value which can be counted by a channel with the chosen integration time."""
        return self._max_count

    def scaled(self):
        """Return a tuple containing the red, green and blue colour values ranging from 0 to 1.0 scaled against the clear value."""
        rgbc = self.raw()
        if rgbc[CH_CLEAR] > 0:
            return tuple([float(x) / rgbc[CH_CLEAR] for x in rgbc])

        return (0,0,0)

    def rgb(self):
        """Return a tuple containing the red, green and blue colour values ranging 0 to 255 scaled against the clear value."""
        return tuple([int(x * 255) for x in self.scaled()][:CH_CLEAR])

    def light(self):
        """Return the clear/unfiltered light level as an integer."""
        return self.raw()[CH_CLEAR]

    def valid(self):
        self.setup()
        return (self.i2c_bus.read_byte_data(ADDR, REG_STATUS) & 1) > 0

    def raw(self):
        """Return the raw red, green, blue and clear channels"""
        self.setup()

        c = self.i2c_bus.read_word_data(ADDR, REG_CLEAR_L)
        r = self.i2c_bus.read_word_data(ADDR, REG_RED_L)
        g = self.i2c_bus.read_word_data(ADDR, REG_GREEN_L)
        b = self.i2c_bus.read_word_data(ADDR, REG_BLUE_L)

        return (r, g, b, c)

    def lux(self):
        """Return the lux (int) [lx]."""
        r = self.raw()[CH_RED]
        g = self.raw()[CH_GREEN]
        b = self.raw()[CH_BLUE]
        c = self.raw()[CH_CLEAR]
        
        ir = (r + g + b - c)/2

        r_ir = r - ir
        g_ir = g - ir
        b_ir = b - ir

        cpl = (self._gain * INTG_TIME_MS)/(TCS_GA * TCS_DF)
        self._lux = int((TCS_R_COEF * r_ir + TCS_G_COEF * g_ir + TCS_B_COEF * b_ir)/cpl)
        return self._lux

    def get_gain(self):
        raw_gain = self.i2c_bus.read_byte_data(ADDR, REG_CONTROL) 
        if raw_gain == REG_CONTROL_GAIN_1X:
            self._gain = 1
        elif self.raw_gain == REG_CONTROL_GAIN_4X:
            self._gain = 4
        elif self.raw_gain == REG_CONTROL_GAIN_16X:
            self._gain = 16 
        elif self.raw_gain == REG_CONTROL_GAIN_60X:
            self._gain = 60 
        print(raw_gain)
        return self._gain


