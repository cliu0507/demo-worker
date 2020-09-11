import cv2
import torch
import segmentation_models_pytorch as smp
from segmentation_models_pytorch.encoders import get_preprocessing_fn
import albumentations as albu

image_path='/home/cliu/Github_cliu/demo-worker/test2.jpg'
image = cv2.imread(image_path)
image = cv2.resize(image,dsize=(512,512))
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


'''
model = smp.Unet('resnet34', encoder_weights='imagenet').cuda()
preprocessing_fn_inference = smp.encoders.get_preprocessing_fn('resnet34', 'imagenet')
'''


def get_preprocessing(preprocessing_fn):
    """Construct preprocessing transform

    Args:
        preprocessing_fn (callbale): data normalization function
            (can be specific for each pretrained neural network)
    Return:
        transform: albumentations.Compose

    """

    _transform = [
        albu.Lambda(image=preprocessing_fn),
        albu.Lambda(image=to_tensor, mask=to_tensor),
    ]
    return albu.Compose(_transform)

def to_tensor(x, **kwargs):
    return x.transpose(2, 0, 1).astype('float32')

preprocessing_inference=get_preprocessing(preprocessing_fn_inference)
sample = preprocessing_inference(image=image, mask=None)
c = sample['image']
d = torch.from_numpy(c).unsqueeze(0).float().cuda()
pr_mask = model.forward(d)
pr_mask = (pr_mask.detach().squeeze().cpu().numpy().round())
cv2.imshow('result', pr_mask)
cv2.waitKey(0)
print('completed!')
