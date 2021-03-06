import sys
import time
import os 
import vrep
from PIL import Image
import array
import numpy as np
import cv2
import matplotlib.pyplot as mlp
import matplotlib.image as mpimg
import perturbation_occlusions as po
import perturbation_lights as pl

## globals
SRV_PORT = 19999
DOF = 6
CAMERA = "Vision_sensor2"
IMAGE_PLANE = "Image_plane"
DIR_LIGHT0 = "Dir_light0"
DIR_LIGHT1 = "Dir_light1"
DIR_LIGHT2 = "Dir_light2"
DIR_LIGHT3 = "Dir_light3"
MAX_LIGHT_INTENSITY = .01
MAX_LIGHT_DISTANCE = .01
MAX_SIGMA = 2
RES_X = 512
RES_Y = 512
N_BASE_IMGS = 3000
N_PERTURBED_IMGS = 1000
subject = 'spoon'
CAPTURED_IMGS_PATH = os.path.join('raw_data', subject, 'original') 
PERTURBED_IMGS_PATH = os.path.join('raw_data', subject, 'perturbed')
LIGHT_PERTURBED_IMGS_PATH = os.path.join('raw_data', subject, 'perturbed_light')
OCCL_PERTURBED_IMGS_PATH = os.path.join('raw_data', subject, 'perturbed_occl')
CAPTURED_GT_PATH = os.path.join('raw_data', subject,'original_GT')
LIGHT_PERTURBED_GT_PATH = os.path.join('raw_data', subject, 'perturbed_light_GT')
OCCL_PERTURBED_GT_PATH = os.path.join('raw_data', subject, 'perturbed_occl_GT')
CAPTURED_FILE_GT_FILE = 'original_GT.csv'
LIGHT_PERTURBED_GT_FILE = 'light_perturbed_GT.csv'
OCCL_PERTURBED_GT_FILE = 'occl_perturbed_GT.csv'


N_SLIC_SEGS = 30

def connect(port, message):
  # connect to server
  vrep.simxFinish(-1)  # just in case, close all opened connections
  clientID = vrep.simxStart('127.0.0.1', 19999, True, True, 5000, 5)  # start a connection
  if clientID != -1:
    print("Connected to remote API server")
    print(message)
  else:
    print("Not connected to remote API server")
    sys.exit("Could not connect")
  return clientID

def getObjectsHandles(clientID, objects):
  handles = {}
  for obj_idx in range(len(objects)):
    err_code, handles[objects[obj_idx]] = vrep.simxGetObjectHandle(clientID, objects[obj_idx], vrep.simx_opmode_blocking)
    if err_code:
      print("Failed to get a handle for object: {}, got error code: {}".format( objects[obj_idx], err_code))
      break;
  return handles

def getLightHandles(clientID, lights):
  handles = {}
  for obj_idx in range(len(lights)):
    err_code, handles[lights[obj_idx]] = vrep.simxGetObjectHandle(clientID, lights[obj_idx], vrep.simx_opmode_blocking)
    if err_code:
      print("Failed to get a handle for object: {}, got error code: {}".format(lights[obj_idx], err_code))
      break;
  return handles

def setCameraInitialPose(clientID, obj):
  # print(obj)
  errPos, position = vrep.simxGetObjectPosition(clientID, obj, -1, vrep.simx_opmode_oneshot_wait)
  # print("1 error", err_code)
  # print("Position", position)

  errOrient, orientation = vrep.simxGetObjectOrientation(clientID, obj, -1, vrep.simx_opmode_oneshot_wait)
  # print("2 error", err_code)
  # print("Orientation", orientation)

  if errPos :
    print("Failed to get position for object: {}, got error code: {}".format(obj, errPos))
  elif errOrient:
    print("Failed to get orientation for object: {}, got error code: {}".format(obj, errOrient))
  else:
    return np.array([position, orientation])

def generateCameraRandomPose(clientID, obj, oldPose):
  # import matplotlib.pyplot as mlp

  randPose = np.asarray(np.random.random([2, 3]))
  # print(randPose)
  # print(np.shape(randPose))

  center = np.array([[0.01, 0.01, 0.01], np.deg2rad([-5, -5, -10])])
  variance = np.array([[0.01, 0.01, 0.01], np.deg2rad([10, 10, 20])])
  std = np.sqrt(variance)

  newPose = np.multiply(randPose, std) - std/2 + oldPose
  # print(np.shape(std))
  # print(oldPose)
  # print(np.shape(newPose))
  return newPose

def setCameraRandomPose(clientID, obj, newPose):
  # print(obj)

  errPos= vrep.simxSetObjectPosition(clientID, obj, -1, newPose[0,:], vrep.simx_opmode_oneshot_wait)
  # print("1 error", err_code)
  # print("Position", position)

  errOrient= vrep.simxSetObjectOrientation(clientID, obj, -1, newPose[1,:], vrep.simx_opmode_oneshot_wait)
  # print("2 error", err_code)
  # print("Orientation", orientation)

  if errPos :
    print("Failed to set position for object: {}, got error code: {}".format(obj, errPos))
  elif errOrient:
    print("Failed to set orientation for object: {}, got error code: {}".format(obj, errOrient))
  else:
    return newPose

def stop(clientID,  message):
  vrep.simxStopSimulation(clientID, vrep.simx_opmode_oneshot)
  print(message)

def renderSensorImage(clientID, camera, fname):
  errRender, resolution, image = vrep.simxGetVisionSensorImage(clientID, camera, 0, vrep.simx_opmode_streaming)
  errRender, resolution, image = vrep.simxGetVisionSensorImage(clientID, camera, 0, vrep.simx_opmode_buffer)


  if errRender == vrep.simx_return_ok:
      img = np.array(image, dtype=np.uint8)
      img.resize([resolution[0], resolution[1], 3])
      img = cv2.flip(img, 0)
      img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
      cv2.imwrite(fname, img)
  pass

def getBBox(object):
  global bbox_x_ext, bbox_y_ext
  errorCodeAll = 0
  errCode, bbox_x_min = vrep.simxGetObjectFloatParameter(clientID, object_handles[object],
                                                         vrep.sim_objfloatparam_objbbox_min_x,
                                                         vrep.simx_opmode_oneshot_wait)
  errorCodeAll = errorCodeAll or errCode
  errCode, bbox_y_min = vrep.simxGetObjectFloatParameter(clientID, object_handles[object],
                                                         vrep.sim_objfloatparam_objbbox_min_y,
                                                         vrep.simx_opmode_oneshot_wait)
  errorCodeAll = errorCodeAll or errCode
  errCode, bbox_z_min = vrep.simxGetObjectFloatParameter(clientID, object_handles[object],
                                                         vrep.sim_objfloatparam_objbbox_min_z,
                                                         vrep.simx_opmode_oneshot_wait)
  errorCodeAll = errorCodeAll or errCode
  errCode, bbox_x_max = vrep.simxGetObjectFloatParameter(clientID, object_handles[object],
                                                         vrep.sim_objfloatparam_objbbox_max_x,
                                                         vrep.simx_opmode_oneshot_wait)
  errorCodeAll = errorCodeAll or errCode
  errCode, bbox_y_max = vrep.simxGetObjectFloatParameter(clientID, object_handles[object],
                                                         vrep.sim_objfloatparam_objbbox_max_y,
                                                         vrep.simx_opmode_oneshot_wait)
  errorCodeAll = errorCodeAll or errCode
  errCode, bbox_z_max = vrep.simxGetObjectFloatParameter(clientID, object_handles[object],
                                                         vrep.sim_objfloatparam_objbbox_max_z,
                                                         vrep.simx_opmode_oneshot_wait)
  if errorCodeAll:
    print("Failed to get bbox for object: {}, got error code: {}".format(IMAGE_PLANE, errorCodeAll))
  else:
    print("pass")
    bbox_x_ext = bbox_x_max - bbox_x_min
    bbox_y_ext = bbox_y_max - bbox_y_min
    bbox_z_ext = bbox_z_max - bbox_z_min

  return [bbox_x_ext, bbox_y_ext, bbox_z_ext]


def peturb_images( n_perturbed_imgs, bbox_ext, perturb_with_light, perturb_with_occl):
  print("Perturbation of images..........................started!")
  
  if perturb_with_light:
    print("Perturbation of images with global lighting..........................started!")
    rel_pose_GT = np.loadtxt(os.path.join(CAPTURED_GT_PATH, CAPTURED_FILE_GT_FILE), dtype=np.float32)
    print("Shape of GT :", rel_pose_GT.shape)

    captured_imgs_fnames = [os.path.join(CAPTURED_IMGS_PATH,f) for f in os.listdir(CAPTURED_IMGS_PATH) if os.path.isfile(os.path.join(CAPTURED_IMGS_PATH, f))]
    n_captured_imgs = len(captured_imgs_fnames)

    print("#captured images : ", n_captured_imgs)
    rand_idx = np.random.choice(np.arange(n_captured_imgs), size = n_perturbed_imgs, replace=False)
    print("Idx picked : ", rand_idx)
   
    captured_imgs_fnames_rand =[captured_imgs_fnames[i] for i in rand_idx]
    rel_pose_light_perturbed_GT = rel_pose_GT[rand_idx, : ]
    lp_img_idx = N_BASE_IMGS
    
    for captured_img_fname_rand in captured_imgs_fnames_rand:
      lights = pl.buildLights(clientID, lights_names, light_handles, MAX_LIGHT_INTENSITY, MAX_LIGHT_DISTANCE, MAX_SIGMA)
      captured_img_rand = cv2.imread(captured_img_fname_rand)
      pl_img = pl.computeLightsContributions(lights, captured_img_rand, bbox_ext, [RES_X, RES_Y])

      fname = os.path.join(LIGHT_PERTURBED_IMGS_PATH, "img" + '_pl_'+'{0:06d}'.format(lp_img_idx) + ".jpg")
      
      cv2.imwrite(fname, pl_img)
      lp_img_idx += 1

    np.savetxt(os.path.join(LIGHT_PERTURBED_GT_PATH, LIGHT_PERTURBED_GT_FILE), rel_pose_light_perturbed_GT, delimiter='\t')
    print("Perturbation of images with global lighting..........................ended!")

  # 2- perturb randomly selected images using occlusion
  if perturb_with_occl:
    print("Perturbation of images with occlusions..........................started!")
    light_perturbed_imgs_fnames = [os.path.join(LIGHT_PERTURBED_IMGS_PATH, f) for f in os.listdir(LIGHT_PERTURBED_IMGS_PATH) if os.path.isfile(os.path.join(LIGHT_PERTURBED_IMGS_PATH, f))]
    n_light_perturbed_imgs = len(light_perturbed_imgs_fnames)
    rel_pose_light_perturbed_GT = np.loadtxt(os.path.join(LIGHT_PERTURBED_GT_PATH, LIGHT_PERTURBED_GT_FILE), dtype=np.float32)
    #light_perturbed_imgs_fnames_rand = np.random.choice(light_perturbed_imgs_fnames, size=n_light_perturbed_imgs, replace=False)
    rand_idx = np.random.choice(np.arange(n_light_perturbed_imgs), size = n_light_perturbed_imgs, replace=False)
    light_perturbed_imgs_fnames_rand = [light_perturbed_imgs_fnames[i] for i in rand_idx]
    rel_pose_occl_perturbed_GT = rel_pose_light_perturbed_GT[rand_idx, : ]
    lp_img_idx = N_BASE_IMGS
    

    po.perturb_with_occl(light_perturbed_imgs_fnames_rand, N_SLIC_SEGS, lp_img_idx,
                         OCCL_PERTURBED_IMGS_PATH, PERTURBED_IMGS_PATH, [RES_Y, RES_X] )

    np.savetxt(os.path.join(OCCL_PERTURBED_GT_PATH, OCCL_PERTURBED_GT_FILE), rel_pose_occl_perturbed_GT, delimiter='\t')
    print("Perturbation of images with occlusions..........................ended!")






if __name__ == "__main__":
  generate_imgs = True
  perturb_with_light = True
  perturb_with_occl = True

  np.random.seed(1234)
  clientID =connect(SRV_PORT, "Data generation started")

  objects_names = [CAMERA, IMAGE_PLANE]
  # lights_names = [DIR_LIGHT0, DIR_LIGHT1, DIR_LIGHT2, DIR_LIGHT3]
  lights_names = [DIR_LIGHT0]
  object_handles = getObjectsHandles(clientID, objects_names)
  # print(object_handles)

  light_handles = getObjectsHandles(clientID, lights_names)
  # print(light_handles)

  if generate_imgs:
    initPose = setCameraInitialPose(clientID, object_handles[CAMERA])
    rel_pose_GT = np.zeros([N_BASE_IMGS, DOF], dtype = np.float32)
    # print(np.shape(initPose))

    poseIdx = 0
    for base_img_idx in range(N_BASE_IMGS):
      print("Creating Pose #{}".format(poseIdx))
      newPose = generateCameraRandomPose(clientID, object_handles[CAMERA], initPose)

      setCameraRandomPose(clientID, object_handles[CAMERA], newPose)
      # print("poseIdx = ", poseIdx)
      fname = os.path.join(CAPTURED_IMGS_PATH, "img"+'{0:06d}'.format(poseIdx) + ".jpg")
      
      rel_pose = newPose - initPose
      rel_pose_GT[poseIdx, 0:3] = rel_pose[0,:]
      rel_pose_GT[poseIdx, 3:6] = rel_pose[1,:]  

      renderSensorImage(clientID, object_handles[CAMERA], fname)
      time.sleep(0.5)
      poseIdx+=1

    np.savetxt(os.path.join(CAPTURED_GT_PATH, CAPTURED_FILE_GT_FILE), rel_pose_GT, delimiter='\t')

  if perturb_with_light or perturb_with_occl:
    bbox_ext = getBBox(IMAGE_PLANE)
    peturb_images(N_PERTURBED_IMGS, bbox_ext, perturb_with_light, perturb_with_occl)

