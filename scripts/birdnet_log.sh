#!/usr/bin/env bash
journalctl --no-hostname -q -o short -fu \
	birdnet_analysis \
	-u birdnet_recording \
	-u birdnet_display_gui \
	-u birdnet_gps \
	-u birdnet_gui_api | sed "s/$(date "+%b %d ")//g;s/${HOME//\//\\/}\///g;/Line/d;/find/d;/systemd/d;s/ .*\[.*\]: /---/"
