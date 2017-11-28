#!/bin/bash
cd .env/lib/python*/site-packages
ln -fns /usr/lib/python3/dist-packages/dbus
ln -fns /usr/lib/python3/dist-packages/_dbus_bindings*
ln -fns /usr/lib/python3/dist-packages/_dbus_glib_bindings*
ln -fns /usr/lib/python3/dist-packages/gi
