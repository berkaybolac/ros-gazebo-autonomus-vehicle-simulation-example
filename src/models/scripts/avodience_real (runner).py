#!/usr/bin/env python
#-*-coding: utf-8 -*-
import numpy as np
import rospy
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


def scancallback(scan):
    
    data = [] #Data 180 derece 720 ornek
    for i in range(18):
        data.append(np.min(np.array(scan.ranges[i*40:(i+1)*40]))) # 40'ar adımlık aralık ile 18 deger aldık.

    mybot_control(np.array(data))
    #print "data : ", data

   

def mybot_control(data):
    if data[0:18].min() > 0.5 and data[0:18].min() < 3.0 : # Robotun onunden 0-180 derece arasına bakıyoruz.
        speed = -1.0
        if data[10:14].min() - data[5:9].min() < 1: # Robotun 100-140 ile 50-90 derece arasındaki farka gore robotu yonlendiriyoruz.
            print "sag"
            speed = -1.0
            angle = 5.0 # neg sol # poz sağ
        else :
            print "sol"
            speed = -1.0    
            angle = -5.0 
        if data[10:14].min() == data[5:9].min():
            speed = -5.0
            angle = 0.0
   
    
    elif data[0:18].min() < 1.0: #robotun engele 1.0 den daha az mesafede ise robotu durdur.
        print "dur"
        speed = 0.0
        angle = 0.0
          
    else :
        print "duz"
        speed = -5.0
        angle = 0.0


    move_cmd.linear.x = speed
    move_cmd.angular.z = angle
    cmd_vel_pub.publish(move_cmd)

def shutdown():
    rospy.loginfo("Stop Mybot")
    cmd_vel_pub.publish(Twist())

if __name__ == '__main__':
    rospy.init_node('pycode', anonymous=True)
    rospy.Subscriber('/laser/scan',LaserScan,scancallback)
    
    rospy.loginfo("To Stop Mybot CTRL + C")
    rospy.on_shutdown(shutdown)
    
    cmd_vel_pub = rospy.Publisher('/r2d2_wheel_controller/cmd_vel',Twist,queue_size=1)
    move_cmd = Twist()
    rospy.spin()