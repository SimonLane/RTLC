import ConfigParser, os

def load_config(self):
    config = ConfigParser.ConfigParser()
    #test for config file
    if os.path.exists('config.cfg'):
        config.read('config.cfg')
        print "Reading config file..."
        self.User_root = config.get('Directory', 'User_root', 0)
        self.Confocal_out = config.get('Directory', 'Confocal_out', 0)
        self.Laser1 = config.get('Lasers', 'Laser1', 0)
        self.Laser2 = config.get('Lasers', 'Laser2', 0)
        self.Laser3 = config.get('Lasers', 'Laser3', 0)
        self.Setup_job = config.get('Jobs', 'Setup_job', 0)
        self.Overview_job = config.get('Jobs', 'Overview_job', 0)
        self.Zoom_job = config.get('Jobs', 'Zoom_job', 0)
    else:
        #if error create config file
        print "No confog file, creating one now"
        config.add_section('Directory')
        config.set('Directory', 'User_root', 'D:\\Experiments')
        config.set('Directory', 'Confocal_out', 'D:\\CAM_STORE\\FromConfocal')
        config.add_section('Jobs')
        config.set('Jobs', 'Setup_job', 'setup')
        config.set('Jobs', 'Zoom_job', 'zoom')
        config.set('Jobs', 'Overview_job', 'OV')
        config.add_section('Lasers')
        config.set('Lasers', 'Laser1', '488')
        config.set('Lasers', 'Laser2', '514')
        config.set('Lasers', 'Laser3', '594')
        config.set('Lasers', 'Laser_limit', '2')
        with open('config.cfg', 'w') as configfile:
            config.write(configfile)
        load_config(self)
            
    

