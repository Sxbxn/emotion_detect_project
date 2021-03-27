# -*- coding: utf-8 -*-
"""resnet_transferlearning.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/17ag69BjGrH4NM4_DF4MAVM1oQ9wnkSlw

# CNN 설계
"""

import torch
import torch.nn as nn
import torchvision
import torch.optim as optim
import torch.nn.functional as F
from torchvision import transforms, datasets, models

USE_CUDA = torch.cuda.is_available()
DEVICE = torch.device("cuda" if USE_CUDA else "cpu")
print(DEVICE)



"""## 하이퍼파라미터 """

EPOCHS     = 30
BATCH_SIZE = 1

"""## 데이터셋 불러오기"""

train_loader = torch.utils.data.DataLoader(
    datasets.CIFAR10('./.data',
                   train=True,
                   download=True,
                   transform=transforms.Compose([
                       transforms.ToTensor(),
                       transforms.Normalize((0.5,),
                                            (0.5,))])),
    batch_size=BATCH_SIZE, shuffle=True)
test_loader = torch.utils.data.DataLoader(
    datasets.CIFAR10('./.data',
                   train=False, 
                   transform=transforms.Compose([
                       transforms.ToTensor(),
                       transforms.Normalize((0.5,),
                                            (0.5,))])),
    batch_size=BATCH_SIZE, shuffle=True)

"""## 모델


"""

# 미리 훈련된 ResNet 모델을 다운로드하고 불러옴
# torchvision.models 참고

import torchvision.models as models

# model = models.resnet50(pretrained=True)
# print(model) # 불러온 모델 구조 확인

class Model(nn.Module):
    def __init__(self):
      super(Model, self).__init__()
      self.conv1 = nn.Conv2d(3, 16, 3)
      self.conv2 = nn.Conv2d(16, 32, 3)
      self.fc1 = nn.Linear(1152, 50)
      self.fc2 = nn.Linear(50, 10)

    def forward(self, x):
      x = F.relu(F.max_pool2d(self.conv1(x), 2))
      x = F.relu(F.max_pool2d(self.conv2(x), 2))
      x = x.view(-1, 1152)
      x = F.relu(self.fc1(x))
      x = self.fc2(x)
      return x

model = Model()

# 제일 마지막 FC layer를 Cifar 클래스에 맞도록 Output 크기 교체 == 즉, resnet.fc를 새로운 nn.Linear를 정의하여 할당.
# 기존 ResNet 모델 FC layer의 in_features값을 할당
#num_input을 nn.Linear에 넣고 수정

# model.fc = nn.Linear(model.fc.in_features, 10)

"""## 준비"""

model.to(DEVICE)

optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)#0.1 vs 0.001
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.1)

"""## 학습하기"""

def train(model, train_loader, optimizer, epoch):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(DEVICE), target.to(DEVICE)
        optimizer.zero_grad()
        output = model(data)
        loss = F.cross_entropy(output, target)
        loss.backward()
        optimizer.step()

"""## 테스트하기"""

def evaluate(model, test_loader):
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(DEVICE), target.to(DEVICE)
            output = model(data)

            # 배치 오차를 합산
            test_loss += F.cross_entropy(output, target,
                                         reduction='sum').item()

            # 가장 높은 값을 가진 인덱스가 바로 예측값
            pred = output.max(1, keepdim=True)[1]
            correct += pred.eq(target.view_as(pred)).sum().item()

    test_loss /= len(test_loader.dataset)
    test_accuracy = 100. * correct / len(test_loader.dataset)
    return test_loss, test_accuracy

"""## 학습"""

for epoch in range(1, EPOCHS + 1):
    train(model, train_loader, optimizer, epoch)
    scheduler.step()
    test_loss, test_accuracy = evaluate(model, test_loader)
    
    print('[{}] Test Loss: {:.4f}, Accuracy: {:.2f}%'.format(
          epoch, test_loss, test_accuracy))