#!/usr/bin/env python
#-*-coding: utf-8 -*-
import numpy as np
import rospy
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


speed = 0

def scancallback(scan):
    
    data = [] #Data 180 derece 720 ornek
    for i in range(18):
        data.append(np.min(np.array(scan.ranges[i*40:(i+1)*40]))) # 40'ar adımlık aralık ile 18 deger aldık.


    
    mybot_control(np.array(data))
    #print "data : ", data




def mybot_control(data):
    

    angle = 5
    if data[8:11].min() > 7:
            print "duz"
            speed = -15.0
            angle = 0
    else:

        if data[2:7].min() > data[12:17].min():
            print "sag yerinde"
            speed -=4
            angle += 5
            #rospy.Rate(5).sleep()        
    
        if data[12:17].min() > data[2:7].min(): 
            print "sol yerinde"
            speed -=4
            angle -= 5
            #rospy.Rate(5).sleep()



        
    
        

    move_cmd.linear.x = speed
    move_cmd.angular.z = angle
    cmd_vel_pub.publish(move_cmd)


def shutdown():
    rospy.loginfo("Stop Mybot")
    cmd_vel_pub.publish(Twist())
    cmd_vel_pub.unregister()

if __name__ == '__main__':
    rospy.init_node('pycode', anonymous=True)
    rospy.Subscriber('/laser/scan',LaserScan,scancallback)
    
    rospy.loginfo("To Stop Mybot CTRL + C")
    rospy.on_shutdown(shutdown)
    
    cmd_vel_pub = rospy.Publisher('/r2d2_wheel_controller/cmd_vel',Twist, tcp_nodelay=False, queue_size=1)
    move_cmd = Twist()
    rospy.spin()
