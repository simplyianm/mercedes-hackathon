#!/usr/bin/env python

import Leap, time, logging ,IPython
from firebase import firebase

class SendGestures:
    def __init__(self):
        """Class initializer"""
        self.init_logger()
        self.init_variables()
        self.init_controller_settings()
        self.get_gesture_loop()

    def init_variables(self):
        """All variables we'd be using in the class"""

        try:
            self.firebase = firebase.FirebaseApplication("https://benz.firebaseio.com/",None)
        except:
            self.log.error("Firebase connection error!!")
            quit()
        self.finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
        self.zoom_flag = False
        self.zoom_origin = 0
        
    def init_controller_settings(self):
        """seeting and config required on the controller for our purpose"""
        self.controller = Leap.Controller()

        self.controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE)
        self.controller.enable_gesture(Leap.Gesture.TYPE_SWIPE)

        self.controller.config.set("Gesture.Circle.MinRadius", 10.0)
        self.controller.config.set("Gesture.Circle.MinArc", 1)
        self.controller.config.save()

    def init_logger(self):
        """setting up the logger"""
        self.log = logging.getLogger("gestures_sent_log")
        hdlr =logging.FileHandler('gestures_sent.log')
        formatter = logging.Formatter('%(message)s')
        hdlr.setFormatter(formatter)
        self.log.addHandler(hdlr) 
        self.log.setLevel(logging.INFO)


    def get_gesture_loop(self):
        self.log.info("started gesture loop")
        count = 0   #we send all false data once every second to make sure that we dont get stuck
        data_previous = None  #used to compare the difference between iterations

        while True:
            count = count+1
            self.gesture_data = {'swipe_right': False,'swipe_left' : False,
                                 'zoom_in' : {'Boolean': False,'Dist': 0} , 'zoom_out': {'Boolean':False, 'Dist': 0},'pinch': False, 'timestamp' : time.asctime() , 'swipe_real_left' : False , 'swipe_real_right' : False,
                                }
            data_all_false = self.gesture_data
            self.frame = self.controller.frame()
            gesture_list = self.frame.gestures()
            hand_list = self.frame.hands

            # Built-in gestures
            for gesture in gesture_list:
                # Circle gesture
                if gesture.type == gesture.TYPE_CIRCLE:
                    if right_hand_exist and len(hand.fingers.extended()) == 1:
                        circle = Leap.CircleGesture(gesture)
                        if (circle.pointable.direction.angle_to(circle.normal) <= Leap.PI/2):
                            self.gesture_data['swipe_left'] = True
                            clockwiseness = "clockwise"
                        else:
                            clockwiseness = "counterclockwise"  
                            self.gesture_data['swipe_right'] = True

                # Swipe gesture
                if gesture.type == gesture.TYPE_SWIPE:
                    swipe = Leap.SwipeGesture(gesture)
                    if swipe.direction[0] > 0:
                        self.gesture_data['swipe_real_right'] = True
                    else:
                        self.gesture_data['swipe_real_left'] = True
            # Custom gestures
            right_hand_exist = False
            for h in hand_list:
                if not h.is_left:
                    hand = h
                    right_hand_exist = True 
            if right_hand_exist:
                finger_list = hand.fingers.extended()
                # Check if the zoom gesture exists in the current frame
                if len(finger_list)==2 and finger_list[0].type==0 and finger_list[1].type==1:
                    if (finger_list[0].direction[0] > 0.0): #y cord of direction of thumb
                        self.gesture_data['zoom_out']['Boolean'] = True
                    elif (finger_list[0].direction[0] < 0.0):
                        self.gesture_data['zoom_in']['Boolean'] = True
                    else:
                        self.log.warn("Thumbs is not positive or negative direction")

                # If there's no zoom gesture in the view, set the flag back to false
                else:
                    self.zoom_flag = False
                if ((hand.pinch_strength == 1) and  ((self.gesture_data['swipe_real_right'] == True) or (self.gesture_data['swipe_real_left'] == True))):
                    self.gesture_data['pinch'] = True

            elif len(hand_list) !=0:
                self.log.warn('Not the right hand!')
            
            self.log.info("before logic data:" +  str(self.gesture_data))

            if data_previous == self.gesture_data:
                if (self.gesture_data['zoom_in']['Boolean'] or self.gesture_data['zoom_out']['Boolean']):
                    snapshot = self.firebase.put('/Datafrompc','leapdata' ,self.gesture_data)
                    self.log.info('Aafter logic data:'+str(self.gesture_data))
                else:
                    pass
            else:
                snapshot = self.firebase.put('/Datafrompc','leapdata' ,self.gesture_data)
                self.log.info('Aafter logic data:' +str(self.gesture_data))
            if count%20 ==0:        
                snapshot = self.firebase.put('/Datafrompc','leapdata' ,data_all_false)
                self.log.info('Aafter logic data'+ str(data_all_false))
                count = 0 
            data_previous =  self.gesture_data
            time.sleep(0.05)
            if not self.controller.is_connected:
                break
        self.log.error("Frame is no longer Valid")

if __name__=="__main__":
    gesture = SendGestures()
