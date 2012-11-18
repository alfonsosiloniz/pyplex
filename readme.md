#Pyplex

##Introduction

The original idea of pyplex is the implementation of an idea on the Plex forums - 
that the Raspberry Pi could use a Plex client that had no interface, and was just 
designed to be operated using an iOS device or similar as a remote. Only the very barest bones
functionality is here, but I hope that it is reasonably easy to extend.

This fork permits the usage of pyplex in the InOut 4G / 4Gs HD DVB-T Mediacenter. It includes an 
API to play videos. We adapt pyplex to use this API instead of the OMXPlayer for Raspberry Pi.


##Before you install

	TO BE DONE

	Python 2.6 has been tested using the ipkg packages from NSLU
	Tornado Python Web server needed to be modifed to avoid epoll/poll calls and using select instead
	DBUS recompiled for 4G/4Gs HD
	AVAHI Daemon needed 

##How to use

Launch with 

    python pyplex.py

