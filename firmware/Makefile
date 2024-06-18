#
# This build environment requires a symbolic link to the AVR libraries and headers
# you are compiling against, roughly like so:
#
# ln -s /usr/local/CrossPack-AVR/avr-4 avr
#

AVRINCLUDEDIR        = $(shell avr-gcc -print-file-name=include)
AVRAVR5DIR           = $(shell avr-gcc -print-file-name=avr5)

PRG                  = spacetime
OBJ                  = main.o uart.o shift.o timer.o display.o keypad.o serial.o clock.o edit.o watchdog.o
PROGRAMMER           = avrisp2
PORT                 = usb
MCU_TARGET           = atmega328p
AVRDUDE_TARGET       = atmega328p
OPTIMIZE             = -Os
DEFS                 = -I$(AVRINCLUDEDIR)
LIBS                 = -L$(AVRAVR5DIR)

HZ                   = 14745600

CC                   = /usr/bin/env avr-gcc

OBJCOPY              = avr-objcopy
OBJDUMP              = avr-objdump

override CFLAGS      =  -g -DF_CPU=$(HZ) -Wall $(OPTIMIZE) -mmcu=$(MCU_TARGET) $(DEFS)
override LDFLAGS     = -Wl,-Map,$(PRG).map

all: $(PRG).elf lst text #eeprom

$(PRG).elf: $(OBJ)
	$(CC) $(CFLAGS) $(LDFLAGS) $(LIBS) -o $@ $^

clean:
	rm -rf *.o $(PRG).elf *.eps *.png *.pdf *.bak *.hex *.bin *.srec
	rm -rf *.lst *.map $(EXTRA_CLEAN_FILES)

lst:  $(PRG).lst

%.lst: %.elf
	$(OBJDUMP) -h -S $< > $@

# Rules for building the .text rom images

text: hex bin srec

hex:  $(PRG).hex
bin:  $(PRG).bin
srec: $(PRG).srec

%.hex: %.elf
	$(OBJCOPY) -j .text -j .data -O ihex $< $@

%.srec: %.elf
	$(OBJCOPY) -j .text -j .data -O srec $< $@

%.bin: %.elf
	$(OBJCOPY) -j .text -j .data -O binary $< $@

# command to program chip (invoked by running "make install")
install:  $(PRG).hex
	avrdude \
        -p $(AVRDUDE_TARGET) \
        -c $(PROGRAMMER) \
        -P $(PORT) \
        -v \
        -U flash:w:$(PRG).hex

# Chip received as lfuse 62, hfuse d9, efuse 7
fuse:
	avrdude \
        -p $(AVRDUDE_TARGET) \
        -c $(PROGRAMMER) \
        -P $(PORT) \
        -v \
        -U lfuse:w:0xd6:m \
        -U hfuse:w:0xdf:m
