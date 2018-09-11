import time
import RPi.GPIO as GPIO
import os
import numpy
read_command_loc='/home/pi/PiShare/commands/from_control/'
write_command_loc='/home/pi/PiShare/commands/from_pi/'

INTERVAL=0.25

def main():


    delme=os.listdir(read_command_loc)
    for file in delme:
        os.remove(read_command_loc+file)
    delme=os.listdir(write_command_loc)
    for file in delme:
        os.remove(write_command_loc+file)
    
    pi_controller=PiController(read_command_loc)
    pi_controller.listen()
    #pi_controller.led_on()
    
class PiController():
    def __init__(self,read_command_loc):
        self.goniometer=Goniometer()
        self.cmdfiles0=[]
        self.cmdnum=0
        self.read_command_loc=read_command_loc
        self.write_command_loc=write_command_loc
        
    def listen(self):
        t=0
        while True:
            self.cmdfiles=os.listdir(self.read_command_loc)  
            if self.cmdfiles==self.cmdfiles0:
                pass
            else:
                for cmdfile in self.cmdfiles:
                    if cmdfile not in self.cmdfiles0:
                        cmd, params=self.decrypt(cmdfile)
                        for x in range(10):
                            cmd=cmd.replace(str(x),'')
                        print(cmd)
                        if cmd=='movetray':
                            print('moving tray')
                            self.goniometer.move_sample(180)
                            filename=self.encrypt('donemoving')
                            self.send(filename)
                            
                        elif cmd=='movearms':
                            print('moving arms')
                            self.goniometer.set_incidence(params[0])
                            self.goniometer.set_emission(params[1])
                            filename=self.encrypt('donemoving')
                            self.send(filename)
                            
                        elif cmd=='movelight':
                            print('moving light')
                            self.goniometer.set_incidence(params[0])
                            filename=self.encrypt('donemoving')
                            self.send(filename)
                            
                        elif cmd=='movedetector':
                            print('moving detector')
                            self.goniometer.set_emission(params[0])
                            filename=self.encrypt('donemoving')
                            self.send(filename)
                            
                        elif cmd=='configure':
                            self.goniometer.configure(params[0],params[1])
                            filename=self.encrypt('piconfigsuccess')
                            self.send(filename)

                        
                            
                        
                        
            self.cmdfiles0=list(self.cmdfiles)
            t=t+INTERVAL
            time.sleep(INTERVAL)
            # if t%3==0:
            #     print('Pi listening!')
            #     print(self.cmdfiles)
        
   #      
    def led_on(self):
        # Use physical pin numbering
        GPIO.setup(18, GPIO.OUT, initial=GPIO.HIGH)  
        
    def send(self,filename):
        try:
            file=open(self.write_command_loc+filename,'w')
        except OSError as e:
            if e.errno==22:
                pass
            else:
                raise e
        except Exception as e:
            raise e
        
    def encrypt(self,cmd,parameters=[]):
        filename=cmd+str(self.cmdnum)
        self.cmdnum+=1
        print(filename)
        for param in parameters:
            param=param.replace('/','+')
            param=param.replace('\\','+')
            param=param.replace(':','=')
            filename=filename+'&'+param
        return filename
        
    def decrypt(self,encrypted):
        cmd=encrypted.split('&')[0]
        params=encrypted.split('&')[1:]
        i=0
        for param in params:
            params[i]=param.replace('+','\\').replace('=',':')
            params[i]=params[i].replace('++','+')
            i=i+1
        return cmd,params
        
    def encrypt(self,cmd,parameters=[]):
        filename=cmd+str(self.cmdnum)
        self.cmdnum+=1
        print(filename)
        for param in parameters:
            param=param.replace('/','+')
            param=param.replace('\\','+')
            param=param.replace(':','=')
            filename=filename+'&'+param
        return filename

class Motor():
    def __init__(self,name,pins,position):
        self.name=name
        self.pins=pins
        self.__position=position
        self.scale=1.2
        self.delay=.012

        
        GPIO.setmode(GPIO.BCM)
        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW) 
        
    @property
    def position(self):
        return self.__position
        
    @position.setter
    def position(self, val):
        val=int(val)
        num_steps=int(numpy.abs(val-self.__position)*self.scale)
        self.forward(num_steps)
        print(self.name+' motor moving from '+str(self.position) +'to '+str(val))
  
        self.__position=val

 
    def forward(self,steps):  
        for i in range(0, steps):
            self.step(1, 0, 0, 0)
            time.sleep(self.delay)
            self.step(0, 1, 0, 0)
            time.sleep(self.delay)
            self.step(0, 0, 1, 0)
            time.sleep(self.delay)
            self.step(0, 0, 0, 1)
            
    def backward(self, steps):  
        for i in range(0, steps):
            self.step(0, 0, 0, 1)
            time.sleep(self.delay)
            self.step(0, 0, 1, 0)
            time.sleep(self.delay)
            self.step(0, 1, 0, 0)
            time.sleep(self.delay)
            self.step(1, 0, 0, 0)
            
    def step(self,w1, w2, w3, w4):
        GPIO.output(self.pins[0], w1)
        GPIO.output(self.pins[1], w2)
        GPIO.output(self.pins[2], w3)
        GPIO.output(self.pins[3], w4)
        
        
class Goniometer():
    def __init__(self):
        self.i_motor=Motor('Incidence',[21,20,16,12],0)
        self.e_motor=Motor('Emission',[25,24,23,18],0)
        self.tray_motor=Motor('Sample tray',[17,5,22,4],0)
    
    def set_incidence(self,theta):
        self.i_motor.position=theta

    def set_emission(self,theta):
        self.e_motor.position=theta
        
    def move_sample(self,diff):
        self.tray_motor.position=self.tray_motor.position+diff
        
    def configure(self,incidence,emission):
        self.i_motor=Motor('Incidence',[21,20,16,12],int(incidence))
        self.e_motor=Motor('Emission',[25,24,23,18],int(emission))
        self.tray_motor=Motor('Sample tray',[17,5,22,4],0)
        print('Configuring to incidence='+incidence+' and emission='+emission)
        
        
if __name__=='__main__':
    main()
    
        
