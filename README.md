# Camera pose estimation using Deep Learning 
Camera pose estimation deals with the problem of estimating the position and orientation of the camera in the 3D space from the pictures taken by it.
This work is still in progress

## Why camera pose estimation?
- Determining where the camera is relative to the object it is looking at is one of the fundamental problems in computer vision and accurately determining the same is the key to applications like augmented reality (AR), autonomous navigation and robot vision. 
- Most solutions to the problem so far require complicated mathematical modelling and are very scene-specific, i.e., a method or framework developed in one scene is likely to fail in another scene. 

## Dependencies
The training and testing of deep networks has been carried out on [Google Colab](https://colab.research.google.com/). 
- Python (=<3.6)
- Tensorflow (1.1x)
- Due to scarcity of labelled datasets, this project used the robotics simulator [CoppeliaSim](https://www.coppeliarobotics.com/) to simulate various viewpoints of a scene while keeping track of the camera position transformation to achieve them. The player version or the educational version may be downloaded from [here](https://www.coppeliarobotics.com/downloads).

## Basic methodology
Using the robotics simulator, several viewpoints of some common indoor and outdoor scenes were simulated with the camera position changes (as measured in 6 degrees of freedom about a known origin) to view them tracked. Deep learning techniques are then used to regress the position of the camera from the images. This method is inspired from [this](https://arxiv.org/abs/1705.08940) CVPR paper. 

## To do
Add references and results
