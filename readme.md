#Pyplex

##Introduction

This is an implementation of an idea on the Plex forums - that the Raspberry Pi
could use a Plex client that had no interface, and was just designed to be 
operated using an iOS device or similar as a remote. Only the very barest bones
functionality is here, but I hope that it is reasonably easy to extend.

##Changes in this version

Plex Media Server transcoding enabled by default. Subtitles now are sent to the MC4G if present in the Media Library. 

TODO: Switch to select whenever to use transcondig

##Before you install

	sudo apt-get update && sudo apt-get upgrade
	sudo wget https://raw.github.com/Hexxeh/rpi-update/master/rpi-update
	sudo cp rpi-update /usr/local/bin/rpi-update
	sudo chmod +x /usr/local/bin/rpi-update 
	sudo rpi-update 192
	sudo reboot
	sudo vim config.txt > to set arm_freq to 1000
	sudo reboot
	sudo apt-get install avahi-daemon
	sudo apt-get install python-pip
	sudo pip install tornado
	sudo pip install pexpect
	sudo apt-get install python-avahi 
	
##How to use

Launch with 

    python pyplex.py [hdmi]

Where [hdmi] is optional to make sure audio is going
over hdmi, leaving it out will devault to the 3,5mm jack output.

Then 'Raspberry Plex' should appear as a player you can choose in your Plex
client. Choose your media, and select this as the player to play it on. It should 
begin playing on your Raspberry Pi! 

I must reiterate how bare-bones this is. Once you start playing the media, you either
wait for it to finish, or 
    
    killall omxplayer.bin
