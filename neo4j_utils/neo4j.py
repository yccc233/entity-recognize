from py2neo import *


class Neo4j:
    def __init__(self):
        try:
            self.graph = Graph("http://localhost:7474", auth=("neo4j", "1111"))
            self.matcher = NodeMatcher(self.graph)
        except:
            print('*-- 请打开neo4j服务 --*')

    def insertNeo4j(self, doubles):
        # 保存到neo4j，参数是一个二维的列表
        print('doubles:{}'.format(doubles))
        try:
            self.graph.delete_all()  # 删除先前的数据，不需要就删掉
            covid = self.matcher.match('covid', name='COVID-19').first()
            if not covid:
                covid = Node('covid', name='COVID-19')
                self.graph.create(covid)
            for dou in doubles:
                # B结点建立
                nodeB = self.matcher.match(dou[2], name=dou[3]).first()
                if not nodeB:
                    nodeB = Node(dou[2], name=dou[3])
                # A结点建立
                if dou[0] == 'covid':
                    rel = Relationship(covid, '有关', nodeB)
                    s = covid | nodeB | rel
                    self.graph.create(s)
                else:
                    nodeA = self.matcher.match(dou[0], name=dou[1]).first()
                    if not nodeA:
                        nodeA = Node(dou[0], name=dou[1])
                    rel = Relationship(nodeA, '有关', nodeB)
                    s = nodeA | nodeB | rel
                    self.graph.create(s)
        except:
            return False, '请打开Neo4j服务！'
        return True, None

    def insertNeo4jRel(self, doubles, rel):
        # 保存到neo4j，参数是一个二维的列表
        print('doubles:{}'.format(doubles))
        if not rel:
            return False, '请先分析文本！'
        try:
            covid = self.matcher.match('covid', name='COVID-19').first()
            if not covid:
                covid = Node('covid', name='COVID-19')
                self.graph.create(covid)
            for dou in doubles:
                # B结点建立
                nodeB = self.matcher.match(dou[2], name=dou[3]).first()
                if not nodeB:
                    nodeB = Node(dou[2], name=dou[3])
                # A结点建立
                if dou[0] == 'covid':
                    relation = Relationship(covid, rel, nodeB)
                    s = covid | nodeB | relation
                    self.graph.create(s)
                else:
                    nodeA = self.matcher.match(dou[0], name=dou[1]).first()
                    if not nodeA:
                        nodeA = Node(dou[0], name=dou[1])
                    relation = Relationship(nodeA, rel, nodeB)
                    s = nodeA | nodeB | relation
                    self.graph.create(s)
        except:
            return False, '请打开Neo4j服务！'
        return True, None

    def deleteRel(self,rel):
        pass


if __name__ == '__main__':
        neo = Neo4j()
        list=[
            ['covid','COVID-19','gene','ACE'],
            ['gene','ACE','phen','发热']
        ]
        neo.insertNeo4j(list)