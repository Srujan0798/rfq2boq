"""Knowledge Graph Builder for RFQ2BOQ.

Builds a graph representation from academic papers, video transcripts, and domain
concepts. Uses Neo4j if available, otherwise falls back to NetworkX.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass, field

try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import AuthError, ServiceUnavailable

    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "rfq2boq"
GRAPH_OUTPUT_DIR = "/Users/srujansai/Desktop/rfq2boq/resources/knowledge_graph"


@dataclass
class Paper:
    name: str
    year: int
    uses_techniques: list[str]
    addresses: list[str]
    extracts: list[str]
    challenges: list[str] = field(default_factory=list)
    performance: str | None = None


PAPERS = [
    Paper(
        name="Zhang & El-Gohary",
        year=2015,
        uses_techniques=["Semantic NLP", "Rule-based extraction"],
        addresses=["Regulatory compliance checking"],
        extracts=["Quantitative requirements"],
        performance="0.80-0.90 precision/recall",
    ),
    Paper(
        name="Sousa et al.",
        year=2024,
        uses_techniques=["NLP", "Text classification", "Computational models"],
        addresses=["Construction budgeting automation"],
        extracts=[],
        challenges=["Subjectivity in human communication"],
    ),
    Paper(
        name="Nabavi et al.",
        year=2023,
        uses_techniques=["NLP", "BIM querying", "Semantic search"],
        addresses=["Quantity Take-Off (QTO)"],
        extracts=[],
        challenges=[],
        performance="BIM + NLP integration",
    ),
    Paper(
        name="Yan et al.",
        year=2022,
        uses_techniques=["Text mining", "Topic modeling (LDA, PLSA)"],
        addresses=["Information extraction/retrieval"],
        extracts=[],
        challenges=["Semantic ambiguity", "Structural characteristics ignored"],
    ),
    Paper(
        name="Zheng et al.",
        year=2023,
        uses_techniques=["Document-level IE", "Event extraction", "Entity extraction"],
        addresses=["Document-level challenges"],
        extracts=[],
        challenges=["Labeling noises", "Entity coreference", "Lack of reasoning"],
    ),
]

TECHNIQUES = [
    "Semantic NLP",
    "Rule-based extraction",
    "NLP",
    "Text classification",
    "Computational models",
    "BIM querying",
    "Semantic search",
    "Text mining",
    "Topic modeling (LDA, PLSA)",
    "Document-level IE",
    "Event extraction",
    "Entity extraction",
    "BERT",
    "BiLSTM",
    "CRF",
    "Transformer models",
]

CONCEPTS = [
    "NER",
    "NLP",
    "BIM",
    "BOQ",
    "Compliance",
    "Extraction",
    "Information Retrieval",
    "Quantity Take-Off",
    "Regulatory compliance",
    "Budgeting automation",
    "Document-level challenges",
]

ENTITY_TYPES = [
    "MATERIAL",
    "QUANTITY",
    "UNIT",
    "LOCATION",
    "DIMENSION",
    "STANDARD",
    "ACTION",
    "GRADE",
]

CHALLENGES = [
    "Regulatory compliance checking",
    "Subjectivity in human communication",
    "Quantity Take-Off (QTO)",
    "Semantic ambiguity",
    "Structural characteristics ignored",
    "Labeling noises",
    "Entity coreference",
    "Lack of reasoning",
    "BIM + NLP integration",
]

DOMAINS = [
    "Construction",
    "NLP",
    "Information Extraction",
    "BIM",
    "Compliance",
]


class Neo4jGraphBuilder:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_graph(self) -> tuple[int, int]:
        nodes = 0
        edges = 0

        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

            for paper in PAPERS:
                session.run(
                    "CREATE (p:Paper {name: $name, year: $year})",
                    name=paper.name,
                    year=paper.year,
                )
                nodes += 1

            for technique in TECHNIQUES:
                session.run(
                    "CREATE (t:Technique {name: $name})",
                    name=technique,
                )
                nodes += 1

            for concept in CONCEPTS:
                session.run(
                    "CREATE (c:Concept {name: $name})",
                    name=concept,
                )
                nodes += 1

            for entity_type in ENTITY_TYPES:
                session.run(
                    "CREATE (e:EntityType {name: $name})",
                    name=entity_type,
                )
                nodes += 1

            for challenge in CHALLENGES:
                session.run(
                    "CREATE (ch:Challenge {name: $name})",
                    name=challenge,
                )
                nodes += 1

            for domain in DOMAINS:
                session.run(
                    "CREATE (d:Domain {name: $name})",
                    name=domain,
                )
                nodes += 1

            for paper in PAPERS:
                for tech in paper.uses_techniques:
                    result = session.run(
                        """
                        MATCH (p:Paper {name: $paper_name})
                        MATCH (t:Technique {name: $tech_name})
                        CREATE (p)-[r:USES_TECHNIQUE {source: $paper_name}]->(t)
                        """,
                        paper_name=paper.name,
                        tech_name=tech,
                    )
                    edges += 1

                for addr in paper.addresses:
                    result = session.run(
                        """
                        MATCH (p:Paper {name: $paper_name})
                        MATCH (ch:Challenge {name: $addr_name})
                        CREATE (p)-[r:ADDRESSES {source: $paper_name}]->(ch)
                        """,
                        paper_name=paper.name,
                        addr_name=addr,
                    )
                    edges += 1

                for ext in paper.extracts:
                    result = session.run(
                        """
                        MATCH (p:Paper {name: $paper_name})
                        MATCH (e:EntityType {name: $ext_name})
                        CREATE (p)-[r:EXTRACTS {source: $paper_name}]->(e)
                        """,
                        paper_name=paper.name,
                        ext_name=ext,
                    )
                    edges += 1

                for chal in paper.challenges:
                    result = session.run(
                        """
                        MATCH (p:Paper {name: $paper_name})
                        MATCH (ch:Challenge {name: $chal_name})
                        CREATE (p)-[r:HAS_CHALLENGE {source: $paper_name}]->(ch)
                        """,
                        paper_name=paper.name,
                        chal_name=chal,
                    )
                    edges += 1

            for concept in CONCEPTS:
                for domain in DOMAINS:
                    if any(
                        domain.lower() in concept.lower() for domain in ["Construction", "NLP", "BIM", "Compliance"]
                    ):
                        session.run(
                            """
                            MATCH (c:Concept {name: $concept_name})
                            MATCH (d:Domain {name: $domain_name})
                            CREATE (c)-[r:PART_OF {source: 'domain_ontology'}]->(d)
                            """,
                            concept_name=concept,
                            domain_name=domain,
                        )
                        edges += 1

        return nodes, edges

    def run_sample_queries(self):
        with self.driver.session() as session:
            print("\n--- Sample Queries ---")

            result = session.run("""
                MATCH (p:Paper)-[r:USES_TECHNIQUE]->(t:Technique)
                RETURN p.name as Paper, collect(t.name) as Techniques
                LIMIT 10
            """)
            print("\nPapers and their techniques:")
            for record in result:
                print(f"  {record['Paper']}: {', '.join(record['Techniques'])}")

            result = session.run("""
                MATCH (p:Paper)-[r:ADDRESSES]->(c:Challenge)
                RETURN p.name as Paper, collect(c.name) as Challenges
                LIMIT 10
            """)
            print("\nPapers addressing challenges:")
            for record in result:
                print(f"  {record['Paper']}: {', '.join(record['Challenges'])}")

            result = session.run("""
                MATCH (p:Paper)-[r:EXTRACTS]->(e:EntityType)
                RETURN p.name as Paper, collect(e.name) as EntityTypes
                LIMIT 10
            """)
            print("\nPapers extracting entity types:")
            for record in result:
                print(f"  {record['Paper']}: {', '.join(record['EntityTypes'])}")


class NetworkXGraphBuilder:
    def __init__(self):
        self.G = nx.DiGraph()

    def create_graph(self) -> tuple[int, int]:
        for paper in PAPERS:
            self.G.add_node(f"Paper:{paper.name}", label="Paper", year=paper.year)

        for technique in TECHNIQUES:
            self.G.add_node(f"Technique:{technique}", label="Technique")

        for concept in CONCEPTS:
            self.G.add_node(f"Concept:{concept}", label="Concept")

        for entity_type in ENTITY_TYPES:
            self.G.add_node(f"EntityType:{entity_type}", label="EntityType")

        for challenge in CHALLENGES:
            self.G.add_node(f"Challenge:{challenge}", label="Challenge")

        for domain in DOMAINS:
            self.G.add_node(f"Domain:{domain}", label="Domain")

        edges_added = 0
        for paper in PAPERS:
            for tech in paper.uses_techniques:
                self.G.add_edge(
                    f"Paper:{paper.name}",
                    f"Technique:{tech}",
                    rel_type="USES_TECHNIQUE",
                    source=paper.name,
                )
                edges_added += 1

            for addr in paper.addresses:
                self.G.add_edge(
                    f"Paper:{paper.name}",
                    f"Challenge:{addr}",
                    rel_type="ADDRESSES",
                    source=paper.name,
                )
                edges_added += 1

            for ext in paper.extracts:
                self.G.add_edge(
                    f"Paper:{paper.name}",
                    f"EntityType:{ext}",
                    rel_type="EXTRACTS",
                    source=paper.name,
                )
                edges_added += 1

            for chal in paper.challenges:
                self.G.add_edge(
                    f"Paper:{paper.name}",
                    f"Challenge:{chal}",
                    rel_type="HAS_CHALLENGE",
                    source=paper.name,
                )
                edges_added += 1

        concept_domain_map = {
            "NER": "Information Extraction",
            "NLP": "NLP",
            "BIM": "BIM",
            "BOQ": "Construction",
            "Compliance": "Compliance",
            "Extraction": "Information Extraction",
            "Information Retrieval": "Information Extraction",
            "Quantity Take-Off": "Construction",
            "Regulatory compliance": "Compliance",
            "Budgeting automation": "Construction",
            "Document-level challenges": "Information Extraction",
        }

        for concept, domain in concept_domain_map.items():
            self.G.add_edge(
                f"Concept:{concept}",
                f"Domain:{domain}",
                rel_type="PART_OF",
                source="domain_ontology",
            )
            edges_added += 1

        for tech1 in TECHNIQUES:
            for tech2 in TECHNIQUES:
                if tech1 != tech2:
                    if any(
                        shared in tech1 or shared in tech2
                        for shared in ["NLP", "extraction", " BERT"]
                        if shared in tech1 and shared in tech2
                    ):
                        pass

        return self.G.number_of_nodes(), edges_added

    def save_to_csv(self, filepath: str):
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["source", "target", "relationship", "source_paper"])
            for u, v, data in self.G.edges(data=True):
                writer.writerow([u, v, data.get("rel_type", ""), data.get("source", "")])

    def print_statistics(self):
        print(f"Nodes: {self.G.number_of_nodes()}")
        print(f"Edges: {self.G.number_of_edges()}")

        print("\nNode counts by type:")
        node_types = {}
        for node in self.G.nodes():
            label = self.G.nodes[node].get("label", node.split(":")[0])
            node_types[label] = node_types.get(label, 0) + 1
        for label, count in sorted(node_types.items()):
            print(f"  {label}: {count}")

    def print_sample_queries(self):
        print("\n--- Sample Queries ---")

        print("\nPapers and their techniques:")
        paper_techs = {}
        for u, v, data in self.G.edges(data=True):
            if data.get("rel_type") == "USES_TECHNIQUE":
                paper = u.replace("Paper:", "")
                tech = v.replace("Technique:", "")
                if paper not in paper_techs:
                    paper_techs[paper] = []
                paper_techs[paper].append(tech)
        for paper, techs in paper_techs.items():
            print(f"  {paper}: {', '.join(techs)}")

        print("\nPapers addressing challenges:")
        paper_challenges = {}
        for u, v, data in self.G.edges(data=True):
            if data.get("rel_type") == "ADDRESSES":
                paper = u.replace("Paper:", "")
                challenge = v.replace("Challenge:", "")
                if paper not in paper_challenges:
                    paper_challenges[paper] = []
                paper_challenges[paper].append(challenge)
        for paper, challenges in paper_challenges.items():
            print(f"  {paper}: {', '.join(challenges)}")

        print("\nPapers extracting entity types:")
        paper_entities = {}
        for u, v, data in self.G.edges(data=True):
            if data.get("rel_type") == "EXTRACTS":
                paper = u.replace("Paper:", "")
                entity = v.replace("EntityType:", "")
                if paper not in paper_entities:
                    paper_entities[paper] = []
                paper_entities[paper].append(entity)
        for paper, entities in paper_entities.items():
            print(f"  {paper}: {', '.join(entities)}")


def main():
    if NEO4J_AVAILABLE:
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            driver.verify_connectivity()
            print("Connected to Neo4j")
            builder = Neo4jGraphBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
            nodes, edges = builder.create_graph()
            print(f"Created {nodes} nodes and {edges} edges in Neo4j")
            builder.run_sample_queries()
            builder.close()
            return
        except (ServiceUnavailable, AuthError) as e:
            print(f"Neo4j not available ({e}), falling back to NetworkX")

    if not NETWORKX_AVAILABLE:
        print("Error: Neither Neo4j nor NetworkX is available")
        sys.exit(1)

    print("Using NetworkX for graph construction")
    builder = NetworkXGraphBuilder()
    nodes, edges = builder.create_graph()
    print(f"Created {nodes} nodes and {edges} edges")

    builder.print_statistics()
    builder.print_sample_queries()

    csv_path = f"{GRAPH_OUTPUT_DIR}/graph_edges.csv"
    builder.save_to_csv(csv_path)
    print(f"\nSaved edge list to {csv_path}")


if __name__ == "__main__":
    main()
