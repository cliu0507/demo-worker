import torch
from torchvision import transforms
from PIL import Image
import matplotlib.pyplot as plt


class WorkflowDeeplabV3(object):
    """
    Official Deeplab V3 demo workflow
    Reference: https://pytorch.org/hub/pytorch_vision_deeplabv3_resnet101/
    """
    def __init__(self):
        self.model = torch.hub.load('pytorch/vision:v0.6.0', 'deeplabv3_resnet101', pretrained=True)
        self.model.eval()
        self.preprocess = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        # move the model to GPU for speed if available
        if torch.cuda.is_available():
            self.model.to('cuda')

        # color palette
        self.palette = torch.tensor([2 ** 25 - 1, 2 ** 15 - 1, 2 ** 21 - 1])
        self.colors = torch.as_tensor([i for i in range(21)])[:, None] * self.palette
        self.colors = (self.colors % 255).numpy().astype("uint8")

    def start(self, input_filepath, output_filepath):
        input_image = Image.open(input_filepath)
        input_tensor = self.preprocess(input_image)
        input_batch = input_tensor.unsqueeze(0)  # create a mini-batch as expected by the model

        # move the input and model to GPU for speed if available
        if torch.cuda.is_available():
            input_batch = input_batch.to('cuda')

        with torch.no_grad():
            output = self.model(input_batch)['out'][0]
        output_predictions = output.argmax(0)

        # plot the semantic segmentation predictions of 21 classes in each color
        r = Image.fromarray(output_predictions.byte().cpu().numpy()).resize(input_image.size)
        r.putpalette(self.colors)
        plt.imsave(output_filepath, r)

    def __str__(self):
        return type(self).__name__
