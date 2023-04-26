README
======

tp370TemperatureMonitor

Project Description:

Installation Guide:

this package includes:
|-- /ProjectFiles/controller.py [A script responsible for threading and joining sensorPoll.py and genVisuals.py. Supports multiple optional arguments for different run cases. See './controller.py --help' for details.]
|-- /ProjectFiles/sensorPoll.py [A non-executable script containing a class that handles polling and recording the sensor readings in file 'defaultRecords.csv'.]
|-- /ProjectFiles/genVisuals.py [A script containing a class that handles image and table generation for the interactive website. Can be tested and run independently. If run with controller.py, will only update concurrently with sensorPoll.py]

|-- /htmlScripts/index.html []
|-- /htmlScripts/current.html []
|-- /htmlScripts/future.html []
|-- /htmlScripts/styles.css []

|-- README.txt [This file]


In order to utilize the Household Temperature Monitor, the user must have set up a hosted or locally run website with a service such as Apache2. This guide will assume you already have a working Apache2 installation, and have properly set up a configuration file for a new website.

1 - Enter supervisor mode. The file system that needs to be changed is set to read only.
2 - Move the contents of /htmlScripts to your document root. (Default is /var/www/html/)
3 - Along with these files, create a symbolic link to where /ProjectFiles is contained. The other scripts save necessary files here.
4 - If the ProjectFiles directory now appears alongside the .html scripts, exit supervisor mode and test your website domain. It is expected that images fail to load.
5 - Execute the ./controller.py script using 'nohup'. If you end your session, the program will continue to execute. You can also view option parameters for your sensor using ./controller.py --help. Example use:
    nohup ./controller.py -v &
6 - The program should have generated some log files in the log directory, and a 'defaultRecords.csv file. These can be checked to ensure the program is running, and may include information if a flag was entered incorrectly.
7 - If successful, the website should automatically populate with data for your current session.
8 - To end your session, kill the process using Ctrl+C, or the 'kill' command. This will ensure all threads have the opportunity to clean up and terminate correctly.
