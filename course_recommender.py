import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import List, Dict, Tuple
import jieba


class CourseEmbedding(nn.Module):
    def __init__(self, vocab_size: int, embedding_dim: int = 32):
        super(CourseEmbedding, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.fc = nn.Linear(embedding_dim, embedding_dim)

    def forward(self, x):
        x = self.embedding(x)
        x = torch.mean(x, dim=0)  # 平均池化
        x = self.fc(x)
        return x


class CourseRecommender:
    def __init__(self, embedding_dim: int = 32):
        self.vocab = set()  # 词汇表
        self.word_to_idx = {}  # 词到索引的映射
        self.embedding_dim = embedding_dim
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def _build_vocab(self, course_names: List[str]):
        """构建词汇表"""
        for name in course_names:
            words = jieba.lcut(name)
            self.vocab.update(words)

        self.word_to_idx = {word: idx for idx, word in enumerate(self.vocab)}
        self.model = CourseEmbedding(len(self.vocab), self.embedding_dim).to(self.device)

    def _text_to_tensor(self, text: str) -> torch.Tensor:
        """将文本转换为张量"""
        words = jieba.lcut(text)
        indices = [self.word_to_idx.get(word, 0) for word in words]
        return torch.tensor(indices, dtype=torch.long).to(self.device)

    def _time_features(self, start_time: str, end_time: str, weekday: str) -> torch.Tensor:
        """将时间信息转换为特征向量"""

        # 将时间转换为分钟数
        def time_to_minutes(time_str):
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes

        start_minutes = time_to_minutes(start_time)
        end_minutes = time_to_minutes(end_time)

        # 将星期转换为数字（1-7）
        weekday_map = {'M': 1, 'T': 2, 'W': 3, 'R': 4, 'F': 5, 'S': 6, 'U': 7}
        weekday_num = weekday_map.get(weekday, 0)

        return torch.tensor([
            start_minutes / (24 * 60),  # 归一化
            end_minutes / (24 * 60),
            weekday_num / 7
        ], dtype=torch.float32).to(self.device)

    def train(self, courses: List[Dict], epochs: int = 100):
        """训练模型
        Args:
            courses: 课程列表，每个课程包含名称、开始时间、结束时间、星期等信息
        """
        # 构建词汇表
        course_names = [course['课程名称'] for course in courses]
        self._build_vocab(course_names)

        # 创建优化器和损失函数
        optimizer = optim.Adam(self.model.parameters())
        criterion = nn.CosineEmbeddingLoss()

        self.model.train()
        for epoch in range(epochs):
            total_loss = 0

            # 为每个课程创建正负样本对
            for i, course in enumerate(courses):
                # 获取当前课程的嵌入
                curr_embedding = self.model(self._text_to_tensor(course['课程名称']))

                # 选择一个相似时间的课程作为正样本
                pos_idx = (i + 1) % len(courses)  # 简单示例，实际应该基于时间相似度选择
                pos_embedding = self.model(self._text_to_tensor(courses[pos_idx]['课程名称']))

                # 随机选择一个不相似的课程作为负样本
                neg_idx = (i + len(courses) // 2) % len(courses)
                neg_embedding = self.model(self._text_to_tensor(courses[neg_idx]['课程名称']))

                # 计算损失
                loss_pos = criterion(curr_embedding.unsqueeze(0),
                                     pos_embedding.unsqueeze(0),
                                     torch.ones(1).to(self.device))
                loss_neg = criterion(curr_embedding.unsqueeze(0),
                                     neg_embedding.unsqueeze(0),
                                     -torch.ones(1).to(self.device))

                loss = loss_pos + loss_neg
                total_loss += loss.item()

                # 反向传播
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            if (epoch + 1) % 10 == 0:
                print(f'Epoch [{epoch + 1}/{epochs}], Loss: {total_loss / len(courses):.4f}')

    def recommend_courses(self, course_name: str, all_courses: List[Dict], top_k: int = 3) -> List[Dict]:
        """推荐相似课程
        Args:
            course_name: 当前课程名称
            all_courses: 所有可选课程
            top_k: 返回前k个推荐课程
        Returns:
            推荐课程列表
        """
        self.model.eval()
        with torch.no_grad():
            # 获取当前课程的嵌入
            curr_embedding = self.model(self._text_to_tensor(course_name))

            # 计算与所有课程的相似度
            similarities = []
            for course in all_courses:
                if course['课程名称'] != course_name:
                    course_embedding = self.model(self._text_to_tensor(course['课程名称']))
                    similarity = torch.cosine_similarity(curr_embedding.unsqueeze(0),
                                                         course_embedding.unsqueeze(0))
                    similarities.append((course, similarity.item()))

            # 返回相似度最高的k个课程
            similarities.sort(key=lambda x: x[1], reverse=True)
            return [course for course, _ in similarities[:top_k]]