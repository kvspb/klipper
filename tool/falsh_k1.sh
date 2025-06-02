openocd -f interface/stlink.cfg -f target/gd32e23x.cfg -c "init" -c "program ./bed_bootloader.bin 0x08000000 verify reset exit"
