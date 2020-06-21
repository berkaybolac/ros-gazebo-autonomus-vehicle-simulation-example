#!/usr/bin/env python2.7


import rospy
import numpy as np
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import cv2
from std_msgs.msg._String import String
import numpy as np
import cv2
import pickle
import os
import tensorflow as tf
from subprocess import call
import keras
import tensorflow as tf1
from tensorflow.python.keras.backend import set_session
from tensorflow.python.keras.models import load_model
from tensorflow.python.client import session


depthBridge = CvBridge()
bgrBridge = CvBridge()


class DepthSender:
    def __init__(self, model, sess):
        self.order = ["20 km/h", "Left forbidden", "Turn left", "Go straight or right", 
        "Turn left", "Go straight or turn left", "Stop", "Turn right", "Park"]
        self.iteration = 0
        self.depth_topic = "/camera/depth/image_raw"
        self.color_topic = "/camera/rgb/image_raw"
        self.count = 0
        self.pub = rospy.Publisher(
            'depthObject', String, tcp_nodelay=False, queue_size=30)
        self.object_distance = "No object"
        self.status = True
        self.x = 0
        self.y = 0
        self.session = sess
        self.model = model
        self.threshold = 0.90
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def grayscale(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        return img

    def equalize(self, img):
        img = cv2.equalizeHist(img)
        return img

    def preprocessing(self, img):
        img = self.grayscale(img)
        img = self.equalize(img)
        img = img/255
        return img

    def getCalssName(self, classNo):

        if classNo == 0:
            return 'Speed Limit 20 km/h %d' % classNo
        elif classNo == 1:
            return 'No left %d' % classNo
        elif classNo == 2:
            return "Stop %d" % classNo
        elif classNo == 3:
            return "Go straight or turn right %d" % classNo
        elif classNo == 4:
            return "Turn left %d" % classNo

    def color_callback(self, color_msg):
        cv_image = depthBridge.imgmsg_to_cv2(color_msg, "passthrough")
        #cv_image = cv_image[20:140, 200:330]
        #if(self.status == True):
         #   self.detect(cv_image)
        cv2.rectangle(cv_image, (self.x, self.y),
                      (self.x-20, self.y+20), (255, 0, 0), 1)
        self.y = 0
        self.x = 0
        cv2.imshow("Color", cv_image)
        cv2.waitKey(1)

    def detect(self, img):
        img = np.asarray(img)
        img = cv2.resize(img, (32, 32))
        img = self.preprocessing(img)
        # cv2.imshow("Processed Image", img)
        img = img.reshape(1, 32, 32, 1)

        try:
            with self.session.as_default():
                with self.session.graph.as_default():
                    predictions = self.model.predict(img)
                    classIndex = self.model.predict_classes(img)
                    probabilityValue = np.amax(predictions)
                    if probabilityValue > self.threshold:

                        # cv2.putText(imgOrignal,str(classIndex)+" "+str(getCalssName(classIndex)), (120, 35), font, 0.75, (0, 0, 255), 2, cv2.LINE_AA)
                        # cv2.putText(imgOrignal, str(round(probabilityValue*100,2) )+"%", (180, 75), font, 0.75, (0, 0, 255), 2, cv2.LINE_AA)
                        print(str(self.getCalssName(classIndex)))
                        print(str(probabilityValue))
                        self.status = False

        except Exception as ex:
            print(ex)

    """
    def depth_callback(self, msg):
        try:
            print("Received an image!")
            cv_image = depthBridge.imgmsg_to_cv2(msg, "passthrough")
            print(cv_image[10, 10])
            image = np.array(cv_image, dtype=np.float)
            cv2.normalize(image, image, 0, 255, cv2.NORM_MINMAX)
            image = np.round(image).astype(np.uint8)
            contours, ret = cv2.findContours(
                image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(cv_image, contours, -1, 255, 3)
            self.shape_detector(contours, cv_image)
            #cv2.imshow("Depth", cv_image)
            # cv2.waitKey(1)
        except CvBridgeError as e:
            print(e) 
    """

    def depth_callback(self, msg):
        try:
            depth_image = depthBridge.imgmsg_to_cv2(msg, "32FC1")
        except CvBridgeError as e:
            print(e)
        depth_array = np.array(depth_image, dtype=np.float32)
        u = msg.height-150
        self.object_distance = "Nothing"
        for t in range(u-10, u+5):
            for x in range(0, len(depth_array[t])):
                if(np.isnan(depth_array[t][x]) == False and not rospy.is_shutdown()):
                    self.status = True
                    self.x = x
                    self.y = t
                    self.object_distance = "{0}".format(self.order[self.iteration])
                    if(self.iteration == len(self.order)):
                        self.iteration = 0
                    else:
                        self.iteration += 1;
        self.pub.publish(data=self.object_distance)

    def shape_detector(self, contours, cv_image):

        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.04 * peri, True)
            print(len(approx))
            if len(approx) == 2:
                return "Probably a line, ground."
            elif(len(approx) >= 6):
                print(len(approx))
                self.status = True
                return True

            else:
                return "Nothing"

    def createSubscriber(self):
        sub = rospy.Subscriber(self.color_topic, Image,
                               self.color_callback, queue_size=1)
        color = rospy.Subscriber(self.depth_topic, Image,
                                 self.depth_callback, queue_size=1)
        rospy.spin()


if __name__ == '__main__':

    config = tf1.ConfigProto(
        device_count={'GPU': 1},
        intra_op_parallelism_threads=1,
        allow_soft_placement=True,
        log_device_placement=True
    )
    config.gpu_options.allow_growth = True
    config.gpu_options.per_process_gpu_memory_fraction = 0.6
    sess = tf.Session(config=config)
    # IMPORTANT: models have to be loaded AFTER SETTING THE SESSION for keras!
    # Otherwise, their weights will be unavailable in the threads after the session there has been set
    keras.backend.set_session(sess)
    pickle_in = open(
        str(os.path.dirname(__file__)) + "/mtrained.p", "rb")
    model = pickle.load(pickle_in)
    model._make_predict_function()
    rospy.init_node('image_listener', anonymous=True)
    sender = DepthSender(model, sess)
    sender.createSubscriber()
