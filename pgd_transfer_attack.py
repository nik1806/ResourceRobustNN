import torch
import argparse
from tqdm import tqdm
from torchvision.datasets import CIFAR10
from torch.utils.data import DataLoader, TensorDataset 
from pytorchcv.model_provider import get_model as ptcv_get_model
from torchattacks import PGD
import torchvision.transforms as transform

def create_attack():

    # dataset
    test_set = CIFAR10('.', train=False, download=True, transform=transform.ToTensor())
    test_loader = DataLoader(test_set, batch_size=32, shuffle=False)

    # load pre-trained model
    model = ptcv_get_model('resnet20_cifar10', pretrained=True)  # 5.97 top-1 error
    model = model.eval().cuda()

    # prepare attack
    atck = PGD(model, eps=8/255, alpha=2/255, steps=10) # same params as in hydra
    atck.set_return_type('int') # Save as integer.
    atck.save(data_loader=test_loader, save_path="./cifar10_pgd.pt", verbose=True)

def test_loop(model, dataloader):
    model = model.cuda().eval()
    corr_pred = 0
    for images, labels in tqdm(dataloader):
        output = model(images.cuda())
        _, prediction = torch.max(output, 1)
        corr_pred += (labels.cuda() == prediction).sum()/ labels.size(0) # .detach().cpu().numpy()

    print(f"Robust accuracy: {100 * corr_pred/len(dataloader):.2f}%")

def eval():
    # Adversarial examples for attack
    adv_images, adv_labels = torch.load("./cifar10_pgd.pt")
    adv_data = TensorDataset(adv_images.float()/255, adv_labels)
    adv_loader = DataLoader(adv_data, batch_size=32, shuffle=False)
    print("Adversarial examples ready !!")
    # Clean dataset
    # test_set = CIFAR10('.', train=False, download=True, transform=transform.ToTensor())
    # adv_loader = DataLoader(test_set, batch_size=32, shuffle=False)

    # load pre-trained model
    # TODO: add support for multiple hydra model
    model = ptcv_get_model('resnet20_cifar10', pretrained=True)  # 5.97 top-1 error
    print("Model ready !!")

    test_loop(model, adv_loader)

        
if __name__ == '__main__':
    # create_attack()
    eval() # clean: 89.15% & robust: 0.05%