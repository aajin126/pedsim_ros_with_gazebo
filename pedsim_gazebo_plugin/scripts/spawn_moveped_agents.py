#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy, re
from gazebo_msgs.srv import SpawnModel
from geometry_msgs.msg import *
from rospkg import RosPack
from pedsim_msgs.msg import AgentStates
from tf.transformations import euler_from_quaternion

def make_actor_xml(xml_src, actor_id, pose):
    # 이름 변경
    xml = re.sub(r'name="actor[^"]*"', f'name="actor_{actor_id}"', xml_src)
    # pose 교체 (actor는 initial_pose 무시됨)
    q = (pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w)
    r, p, y = euler_from_quaternion(q)
    pose_line = f'<pose>{pose.position.x} {pose.position.y} {pose.position.z} {r} {p} {y}</pose>'
    xml = re.sub(r'<pose>.*?</pose>', pose_line, xml, flags=re.DOTALL)
    # agent_id 주입
    xml = re.sub(r'</plugin>', f'  <agent_id>{actor_id}</agent_id>\n  </plugin>', xml, count=1)
    return xml

def actor_poses_callback(actors):
    for actor in actors.agent_states:
        actor_id = str(actor.id)
        rospy.loginfo("Spawning actor %s", actor_id)
        xml_per_actor = make_actor_xml(xml_string, actor_id, actor.pose)
        spawn_model(actor_id, xml_per_actor, "", Pose(), "world")
    rospy.signal_shutdown("spawn done")

if __name__ == '__main__':
    rospy.init_node("spawn_pedsim_actors")
    rospack = RosPack()
    pkg_path = rospack.get_path('pedsim_gazebo_plugin')
    default_sdf = pkg_path + "/models/actor1/sdf/actor1.sdf"

    actor_file = rospy.get_param('~actor_model_file', default_sdf)
    with open(actor_file) as f:
        xml_string = f.read()

    rospy.wait_for_service("gazebo/spawn_sdf_model")
    spawn_model = rospy.ServiceProxy("gazebo/spawn_sdf_model", SpawnModel)
    rospy.Subscriber("/pedsim_simulator/simulated_agents", AgentStates, actor_poses_callback)
    rospy.spin()

