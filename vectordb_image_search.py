import pickle
import chromadb
import pandas as pd
import numpy as np
import random
import json
import time
import os

from pathlib import Path

class ChromaJob:
    def __init__(self):
        self.db_path = None
        self.dataset_path = None
        self.db_size = None
        self.client = None
        self.client_collection = None

    def set_db_path(self, db_path):
        self.db_path = db_path
    def set_dataset_path(self, dataset_path):
        self.dataset_path = dataset_path
    def set_db_size(self, db_size):
        self.db_size = db_size
    def set_collection_name(self, collection_name):
        self.collection_name = collection_name
        
    def calc_db_Size(self):
        db_path = self.db_path
        return sum(os.path.getsize(os.path.join(db_path, f)) for f in os.listdir(db_path))

    def db_init(self, db_path, dataset_path):
        self.set_db_path(db_path=db_path)
        self.dataset_path(dataset_path=dataset_path)
        self.set_db_size(db_size=self.calc_db_Size())

    def insert_dataset(self):
        start = time.time()
        with open(self.dataset_path, 'rb') as file:
            df = pickle.load(file)
        start2 = time.time()
        if self.client is not None and self.client_collection is not None:
            for i in range(len(df)):
                row = df.iloc[i]
                face_name = row['name']
                face_path = row['path']
                face_id = Path(face_path).stem  # 파일명을 id로 사용
                face_embedding = row['embedding']

                try:
                    self.client_collection.add(
                        embeddings=[face_embedding],
                        metadatas=[{
                            'name': face_name,
                            'path': face_path
                        }],
                        ids=[face_id]
                    )
                except Exception as e:
                    print(f"Error inserting data at index {i}: {e}")
        return time.time() - start, time.time() - start2
    
    def clinet_on(self):
        if self.client is None :
            self.client = chromadb.PersistentClient(path=self.db_path)
        else : pass

        if self.client_collection is None :
            self.client_collection = self.client.get_or_create_collection(name=self.collection_name)
        else : pass
    
    def randomly_query(self,n_results):
        with open(self.dataset_path, 'rb') as file:
            df = pickle.load(file)

        rand_num = random.randint(0, len(df)-1)
        test_emb = df.iloc[rand_num]['embedding']
        try:
            start = time.time()
            query_result = self.client_collection.query(
                query_embeddings=[test_emb],
                n_results=n_results
            )
            #print(json.dumps(query_result, ensure_ascii=False, indent=3))
            return time.time() - start, None
        except Exception as e:
            print(e)
            return time.time() - start, e

# chroma = ChromaJob()
# chroma.set_db_path(r'/Users/jang-yeong-u-macmini/Desktop/prom_client')
# chroma.set_dataset_path(r'/Users/jang-yeong-u-macmini/Desktop/prom_client/lfw_face_dataset')
# chroma.set_collection_name('lfw_faces')
# chroma.clinet_on()
# # A = chroma.insert_dataset()
# # print(A)
# B = chroma.randomly_query(n_results=1000)
# print(B)



# # 데이터베이스 경로 설정
# db_path = r'/Users/jang-yeong-u-macmini/Desktop/prom_client'
# db_size = sum(os.path.getsize(os.path.join(db_path, f)) for f in os.listdir(db_path))

# print(f"Current database size: {db_size} bytes")

# # lfw 벡터 임베딩 데이터셋 로드
# with open(r'/Users/jang-yeong-u-macmini/Desktop/prom_client/lfw_face_dataset', 'rb') as file:
#     df = pickle.load(file)

# # 데이터 확인
# print("############################# check dataset ###############################")
# print("dataset row count: " + str(len(df)))
# print(df.tail())

# # Chroma 클라이언트 설정
# client = chromadb.PersistentClient(path=db_path)

# # 클라이언트 확인
# print("############################# chromadb availability ###############################")
# print(client.heartbeat())

# # 컬렉션 생성 또는 가져오기
# collection = client.get_or_create_collection(
#     name='lfw_faces'
# )

# # 컬렉션 내 데이터 개수 확인
# print("############################# check saved data ###############################")
# print(collection.count())

# # 데이터 삽입
# print("############################# insert dataset ###############################")
# for i in range(len(df)):
#     row = df.iloc[i]
#     face_name = row['name']
#     face_path = row['path']
#     face_id = Path(face_path).stem  # 파일명을 id로 사용
#     face_embedding = row['embedding']

#     try:
#         collection.add(
#             embeddings=[face_embedding],
#             metadatas=[{
#                 'name': face_name,
#                 'path': face_path
#             }],
#             ids=[face_id]
#         )
#     except Exception as e:
#         print(f"Error inserting data at index {i}: {e}")

# print("############################# input data ###############################")
# # 검색할 얼굴 랜덤 선택
# rand_num = random.randint(0, len(df)-1)
# test_emb = df.iloc[rand_num]['embedding']
# test_id = df.iloc[rand_num]['path']
# test_name = df.iloc[rand_num]['name']
# print("rand_num: {}, id: {}, name: {}".format(rand_num, test_id, test_name))

# print("############################# result ###############################")
# # 가장 가까운 항목 조회
# start_time = time.time()
# query_result = collection.query(
#     query_embeddings=[test_emb],
#     n_results=5
# )
# end_time = time.time()
# #print(json.dumps(query_result, ensure_ascii=False, indent=3))
# print(f"Query time: {end_time - start_time} seconds")