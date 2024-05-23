from math import sqrt
import numpy as np
from peewee import Model, PostgresqlDatabase, fn
from pgvector.peewee import VectorField

db = PostgresqlDatabase('pgvector_python_test')


class BaseModel(Model):
    class Meta:
        database = db


class Item(BaseModel):
    embedding = VectorField(dimensions=3)


Item.add_index('embedding vector_l2_ops', using='hnsw')

db.connect()
db.execute_sql('CREATE EXTENSION IF NOT EXISTS vector')
db.drop_tables([Item])
db.create_tables([Item])

class Item2(BaseModel):
    embedding = VectorField(dimensions=2)


Item2.add_index('embedding vector_l2_ops', using='hnsw')

db.drop_tables([Item2])
db.create_tables([Item2])



def create_items():
    vectors = [
        [1, 1, 1],
        [2, 2, 2],
        [1, 1, 2]
    ]
    for i, v in enumerate(vectors):
        Item.create(id=i + 1, embedding=v)


class TestPeewee:
    def setup_method(self, test_method):
        Item.truncate_table()

    def test_works(self):
        Item.create(id=1, embedding=[1, 2, 3])
        item = Item.get_by_id(1)
        assert np.array_equal(item.embedding, np.array([1, 2, 3]))
        assert item.embedding.dtype == np.float32

    def test_l2_distance(self):
        create_items()
        distance = Item.embedding.l2_distance([1, 1, 1])
        items = Item.select(Item.id, distance.alias('distance')).order_by(distance).limit(5)
        assert [v.id for v in items] == [1, 3, 2]
        assert [v.distance for v in items] == [0, 1, sqrt(3)]

    def test_mahalanobis_distance(self):
        query_vectors = np.array([
            [2, 0],
            [-2, 0],
            [0, 8]
        ])
        mean = np.mean(query_vectors, axis=0)

        vectors = [
            mean,
            mean + [2.1, 0],
            mean + [0, 2.2]
        ]
        for i, v in enumerate(vectors):
            Item2.create(id=i + 1, embedding=v)

        print(np.cov(query_vectors, rowvar=False))
        matrix = np.linalg.inv(np.cov(query_vectors, rowvar=False))

        mahal = Item2.embedding.mahalanobis_distance(matrix)
        items = Item2.select(Item2.id, mahal.alias('distance')).order_by(mahal).limit(5)
        assert [v.id for v in items] == [1, 3, 2]
        print([v.distance for v in items])
        assert [v.distance for v in items] == [6.0, 12.0, 18.0]

    def test_max_inner_product(self):
        create_items()
        distance = Item.embedding.max_inner_product([1, 1, 1])
        items = Item.select(Item.id, distance.alias('distance')).order_by(distance).limit(5)
        assert [v.id for v in items] == [2, 3, 1]
        assert [v.distance for v in items] == [-6, -4, -3]

    def test_cosine_distance(self):
        create_items()
        distance = Item.embedding.cosine_distance([1, 1, 1])
        items = Item.select(Item.id, distance.alias('distance')).order_by(distance).limit(5)
        assert [v.id for v in items] == [1, 2, 3]
        assert [v.distance for v in items] == [0, 0, 0.05719095841793653]

    def test_where(self):
        create_items()
        items = Item.select().where(Item.embedding.l2_distance([1, 1, 1]) < 1)
        assert [v.id for v in items] == [1]

    def test_avg(self):
        avg = Item.select(fn.avg(Item.embedding)).scalar()
        assert avg is None
        Item.create(embedding=[1, 2, 3])
        Item.create(embedding=[4, 5, 6])
        avg = Item.select(fn.avg(Item.embedding)).scalar()
        assert np.array_equal(avg, np.array([2.5, 3.5, 4.5]))

    def test_sum(self):
        sum = Item.select(fn.sum(Item.embedding)).scalar()
        assert sum is None
        Item.create(embedding=[1, 2, 3])
        Item.create(embedding=[4, 5, 6])
        sum = Item.select(fn.sum(Item.embedding)).scalar()
        assert np.array_equal(sum, np.array([5, 7, 9]))

    def test_get_or_create(self):
        Item.get_or_create(id=1, defaults={'embedding': [1, 2, 3]})
        Item.get_or_create(embedding=np.array([4, 5, 6]))
        Item.get_or_create(embedding=Item.embedding.to_value([7, 8, 9]))
