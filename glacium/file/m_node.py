# !/usr/bin/env python
"""Title.

Description
"""
# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from itertools import count, product
from typing import Any, List, Dict
from copy import deepcopy
from abc import ABC, abstractmethod
import random
import coloredlogs
import verboselogs
import yaml
from interface import Interface
import matplotlib as plt
from m_submodules import Logger, Identify, setup_coloredlogs
from meta_statistics import SingletonMeta
import networkx as nx
from statistics import mean
# -----------------------------------------------------------------------------
# COPYRIGHT
# -----------------------------------------------------------------------------
__author__ = "Noel Ernsting Luz"
__copyright__ = "Copyright (C) 2022 Noel Ernsting Luz"
__license__ = "Public Domain"
__version__ = "1.0"
# -----------------------------------------------------------------------------
# LOGGER
# -----------------------------------------------------------------------------
G = nx.Graph()
from pyvis.network import Network

setup_coloredlogs()
verboselogs.install()
logger = verboselogs.VerboseLogger(__name__)
coloredlogs.install(level="spam", logger=logger)


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------


class NodeRegistry(Interface):

    def __init__(self, registry: List[Node] = None):
        # Load submodules
        self.logger = Logger[self]()
        self.registry: List[Node]

        # Initiate from specified list
        if registry:
            self.registry: List[Node] = list(registry)
        else:
            self.registry: List[Node] = list([])

    def register_node(self, node: Node) -> None:
        self.registry.append(node)

    def handle_resolve(self, tag) -> Node:
        # Initialization of the function
        SECURE_CACHE: list = []
        result: Node = None

        # Compare identities
        for node in self:
            if node.identity is tag:
                result = node
                SECURE_CACHE.append(node)

        # Verify
        # self.logger.debug(f"Assessment: {len(SECURE_CACHE)} for {SECURE_CACHE}")
        assert len(SECURE_CACHE) < 2, "Multiple nodes detected."
        assert len(SECURE_CACHE) != 0, "No match for requested identity."

        return result

    def inspect(self) -> None:
        self.logger.info("#" * 40 + " INSPECTION " + "#" * 40)
        self.logger.verbose(f"{type(self).__name__}:")
        [self.logger.debug(node) for node in self]
        self.logger.info("#" * 40 + " INSPECTION " + "#" * 40)

    def is_root(self):
        results = []
        for node in self.registry:
            if node.is_root():
                results.append(node)
        return NodeRegistry(results)

    def is_base_variant(self) -> NodeRegistry:
        results = []
        for node in self.registry:
            if node.is_configurable():
                if node.is_base_variant():
                    results.append(node)
        return NodeRegistry(results)

    def is_configurable(self) -> NodeRegistry:
        results = []
        for node in self.registry:
            if node.is_configurable():
                results.append(node)
        return NodeRegistry(results)

    def __getitem__(self, index: int) -> Node:
        return self.registry[index]

    def __iter__(self):
        return self.registry.__iter__()

    def __len__(self):
        return len(self.registry)

    def __repr__(self):
        return f"TYPE: {type(self).__name__} - MEMBERS: {len(self)}"

    def __str__(self):
        return f"TYPE: {type(self).__name__} - MEMBERS: {len(self)}"


class ApexRegistry(NodeRegistry, metaclass=SingletonMeta):
    def configurability(self) -> list:
        nodes = self.is_root().is_configurable()
        results = []
        for root in nodes:
            tree = root.gen_semi_tree().is_configurable()
            tree.registry.remove(root)
            res = []
            for node in tree:
                if node.is_base_variant():
                    variants = node.list_variants()
                    res.append([variant.variant_tag for variant in variants])

            res = list(product((root.variant_tag,), *res))
            results.append(res)
        return results


class Node(Interface):

    def __init__(self, name: str = None) -> None:
        # load submodules
        self.logger: Logger = Logger[self]()
        self.identity: Identify = Identify[self](name)

        # load specific attributes
        self.node_registry: List[Identify] = []
        self.link_registry: Dict[str, Identify] = {}
        self.back_registry: List[Identify] = []

        # Secondary attributes
        self.data_registry: Dict[str, Any] = {}
        self.apex_registry: ApexRegistry = ApexRegistry()

        # Operational initialization
        self.logger.set_level("SPAM")
        self.active_variant = "base"
        self.variant_tag = self.identity.dogtag + ("base",)
        self.link_registry.update({"base": self.identity})
        self.apex_registry.register_node(self)

        # log specific information
        self.logger.verbose(f"Initiation protocol finished. "
                            f"Created Node: {self.identity}")

    def is_configurable(self) -> bool:
        return len(self.link_registry) > 1

    def is_base_variant(self) -> bool:
        return self.link_registry["base"] == self.identity

    def is_root(self) -> bool:
        variants = self.list_variants()
        result = None
        for node in variants:
            if node.back_registry:
                return False
        return True

    def is_active_variant(self) -> bool:
        return self.link_registry[self.active_variant] == self.identity

    def paternity_test(self, child: Node) -> bool:
        origin = self.gen_semi_tree()
        if child in origin.registry:
            if child != self:
                return True
        return False

    def variant_reachability(self, child: Node) -> bool:
        origin = self.gen_semi_tree()
        assert child.is_configurable(), "child is not configurable"
        res = []
        for node in child.list_variants():
            if node in origin.registry:
                res.append(True)
        return all(res)

    def get_variant_name(self) -> str:
        link_registry_inv = {v: k for k, v in self.link_registry.items()}
        name = link_registry_inv[self.identity]
        return name

    def list_variants(self) -> List[Node]:
        variants: List[Node] = []

        for tag in self.link_registry.values():
            variants.append(self.resolve(tag))

        return variants

    def list_variant_names(self) -> List[str]:
        return list(self.link_registry.keys())

    def create_variant(self, name: str) -> None:
        # [STEP 01]: Copy my subtree
        cloned_root = self.gen_copy()[0]

        # [STEP 02]: Copy my subtree
        self.link_registry.update({name: cloned_root.identity})
        for tag in self.link_registry.values():
            node = self.resolve(tag)
            node.link_registry = self.link_registry
            node.variant_tag = (node.identity,) + (node.get_variant_name(),)

        self.logger.verbose(f"Created variant '{name}' of {self.identity}")

    def activate_variant(self, name: str) -> Node:
        variant = self.resolve(self.link_registry[name])

        self.active_variant = name

        for tag in self.back_registry:
            node = self.resolve(tag)
            node.attach(variant)
            node.detach(self)

        for node in self.list_variants():
            node.active_variant = name
        self.logger.verbose(f"Activated variant '{name}' of {self.identity}")
        return variant

    def attach(self, node: Node) -> None:
        self.node_registry.append(node.identity)
        node.back_registry.append(self.identity)

    def detach(self, node: Node) -> None:
        self.node_registry.remove(node.identity)
        node.back_registry.remove(self.identity)

    def register(self, **kwargs) -> None:
        self.data_registry.update(kwargs)

    def resolve(self, tag) -> Node:
        return self.apex_registry.handle_resolve(tag)

    def gen_tree(self) -> NodeRegistry:
        members = []
        next_level = [self]

        while next_level:

            this_level = list(next_level)
            next_level = []

            for node in this_level:

                members.append(node)

                for child in node:
                    next_level.append(child)

        return NodeRegistry(members)

    def gen_semi_tree(self) -> NodeRegistry:
        members = []

        next_level = [self]

        while next_level:

            this_level: List[Node] = list(next_level)
            next_level: List[Node] = []

            for node in this_level:
                members.append(node)

                for child in node:
                    next_level.append(child)
                    if child.is_configurable():
                        variants = child.list_variants()
                        variants.remove(child)
                        next_level.extend(variants)

        return NodeRegistry(members)

    def gen_deep_tree(self) -> NodeRegistry:
        members = []
        next_level = self.list_variants()

        while next_level:

            this_level: List[Node] = list(next_level)
            next_level: List[Node] = []

            for node in this_level:

                # Data transformation:
                members.append(node)

                # Acquisition code.
                # This makes sure, you get ALL the nodes in a tree.
                for child in node:
                    next_level.append(child)
                    if child.is_configurable():
                        variants = child.list_variants()
                        variants.remove(child)
                        next_level.extend(variants)

        return NodeRegistry(members)

    def gen_config(self):
        members = []
        next_level = self.list_variants()

        while next_level:

            this_level: List[Node] = list(next_level)
            next_level: List[Node] = []
            this_layer: List[Node] = []

            for node in this_level:

                # Data transformation:
                if node.is_base_variant() and node.is_configurable():
                    this_layer.append(node.variant_tag)

                # Acquisition code.
                # This makes sure, you get ALL the nodes in a tree.
                for child in node:
                    next_level.append(child)
                    if child.is_configurable():
                        variants = child.list_variants()
                        variants.remove(child)
                        next_level.extend(variants)
            if this_layer:
                members.append(this_layer)

        return members

    def gen_copy(self) -> NodeRegistry:
        origin = self.gen_tree()
        clones = []

        # Copying all local variables
        for node in origin:
            clones.append(Node(node.identity.name))

        # Copying registration data
        for node in origin:
            node_index = origin.registry.index(node)
            for child in node:
                child_index = origin.registry.index(child)
                cloned_node = clones[node_index]
                cloned_child = clones[child_index]
                cloned_node.attach(cloned_child)

        return NodeRegistry(clones)

    def estimate_configurations(self) -> int:
        configurations = self.gen_config()
        total_size = 1
        for layer in configurations:
            layer_size = 1
            for node in layer:
                size = len(ApexRegistry().handle_resolve(node[0]).link_registry)
                layer_size *= size
            total_size *= layer_size

        return total_size

    def inspect(self) -> None:
        self.logger.set_level("SPAM")
        self.logger.info("#" * 30 + " INSPECTION " + "#" * 30)
        self.logger.verbose(f"{type(self).__name__}:")
        self.logger.debug(f"{self.identity}")
        self.logger.verbose(f"Members:")
        [self.logger.debug(f"{tag}".ljust(30) + f"{self.resolve(tag).data_registry['name'] if self.resolve(tag).data_registry['name'] else ''}".ljust(80) + f"{self.resolve(tag).data_registry['price'] if self.resolve(tag).data_registry['price'] else ''}") for tag in self.node_registry]
        self.logger.verbose(f"Total:")
        price = 0.0
        for node in self.gen_tree():
            node: Node
            if "price" in node.data_registry:
                price += node.data_registry["price"]
        self.logger.error(f"{price}")
        self.logger.verbose(f"Variants:")
        [self.logger.debug(f"{key}".ljust(20) + f" : {value}") for key, value
         in self.link_registry.items()]
        self.logger.verbose(f"Flags:")
        self.logger.debug(f"is_configurable: {self.is_configurable()}")
        self.logger.debug(f"is_active_variant: {self.is_active_variant()}")
        self.logger.debug(f"is_base_variant: {self.is_base_variant()}")
        self.logger.verbose(f"Active:")
        self.logger.debug(f"{self.active_variant}")
        self.logger.info("#" * 30 + " INSPECTION " + "#" * 30)
        self.logger.set_level("CRITICAL")


    def __getitem__(self, name: str) -> Node:
        # Initialization of the function
        secure_cache: list = []

        # Commencing search for name in own registry
        for node in self:
            if node.identity.name is name:
                secure_cache.append(node)

        # Verify
        assert len(secure_cache) == 1, "Multiple nodes detected"
        return secure_cache[0]

    def __iter__(self) -> Node:
        self._index = 0
        return self

    def __next__(self) -> Node:
        if self._index is len(self.node_registry):
            raise StopIteration

        element = self.node_registry[self._index]

        self._index += 1
        return self.resolve(element)

    def __len__(self) -> int:
        return len(self.node_registry)

    def __repr__(self) -> str:
        return f"{type(self).__name__}" + \
               f" - TAG: {self.identity.dogtag}".ljust(25) + \
               f" - SIZE: {len(self.gen_semi_tree())}".ljust(12) + \
               f" - NAME: {self.get_variant_name()}".ljust(20) + \
               f" - ACTV: {self.active_variant}"

    def __str__(self) -> str:
        return f"{type(self).__name__}" + \
               f" | TAG: {self.identity.dogtag}".ljust(25) + \
               f" | SIZE: {len(self.gen_semi_tree())}".ljust(12) + \
               f" | NAME: {self.get_variant_name()}".ljust(20) + \
               f" | ACTV: {self.active_variant}"


def main():
    computer = Node("computer")
    computer.attach(Node("psu"))
    computer.attach(Node("cpu"))
    computer.attach(Node("ram"))
    computer.attach(Node("disk"))
    computer.attach(Node("cooling"))
    computer.attach(Node("mainboard"))
    computer.attach(Node("gpu"))
    computer.attach(Node("case"))
    computer.attach(Node("monitor"))
    computer.attach(Node("fan"))

    computer["psu"].register(name="750 Watt be quiet! Straight Power 11 Modular 80+ Gold", price=109.89)
    computer["psu"].create_variant("variant_1")
    computer["psu"].activate_variant("variant_1").register(name="750 Watt be quiet! Pure Power 11 FM Modular 80+ Gold", price=100.89)
    computer["psu"].create_variant("variant_2")
    computer["psu"].activate_variant("variant_2").register(name="850 Watt be quiet! Pure Power 11 FM Modular 80+ Gold", price=113.94)

    computer["cpu"].register(name="AMD Ryzen 7 5700X 8x 3.40GHz So.AM4 WOF", price=279.0)
    computer["cpu"].create_variant("variant_1")
    computer["cpu"].activate_variant("variant_1").register(name="AMD Ryzen 7 5700X 8x 3.80GHz So.AM4 WOF", price=299.0)
    computer["cpu"].create_variant("variant_2")
    computer["cpu"].activate_variant("variant_2").register(name="AMD Ryzen 9 5900X 12x 3.70GHz So.AM4 WOF", price=399.0)

    computer["ram"].register(name="32GB G.Skill RipJaws V schwarz DDR4-3200 DIMM CL16 Dual Kit", price=108.39)
    computer["ram"].create_variant("variant_1")
    computer["ram"].activate_variant("variant_1").register(name="16GB G.Skill RipJaws V schwarz DDR4-3600 DIMM CL18 Dual Kit", price=60.19)
    computer["ram"].create_variant("variant_2")
    computer["ram"].activate_variant("variant_2").register(name="16GB G.Skill RipJaws V schwarz DDR4-3600 DIMM CL16 Dual Kit Aktiv PCIe 4.0 x16)", price=82.33)

    computer["disk"].register(name="1TB Samsung SSD 980 M.2 PCIe 3.0 x4 3D-NAND TLC (MZ-V8V1T0BW)", price=88.0)
    computer["disk"].create_variant("variant_1")
    computer["disk"].activate_variant("variant_1").register(name="1TB Samsung 970 Evo Plus M.2 2280 PCIe 3.0 x4 NVMe 1.3 3D-NAND TLC (MZ-V7S1T0BW)", price=109.0)
    computer["disk"].create_variant("variant_2")
    computer["disk"].activate_variant("variant_2").register(name="1TB Crucial P2 M.2 PCIe 3.0 x4 3D-NAND QLC (CT1000P2SSD8)", price=67.50)

    computer["cooling"].register(name="be quiet! Pure Loop 360mm All-in-One", price=111.89)
    computer["cooling"].create_variant("variant_1")
    computer["cooling"].activate_variant("variant_1").register(name="be quiet! Pure Loop 240mm All-in-One", price=79.89)
    computer["cooling"].create_variant("variant_2")
    computer["cooling"].activate_variant("variant_2").register(name="Arctic Liquid Freezer II 360 All-in-One", price=95.79)

    computer["mainboard"].register(name="MSI B450 Gaming Plus MAX AMD B450 So.AM4 Dual Channel DDR4 ATX Retail", price=78.0)
    computer["mainboard"].create_variant("variant_1")
    computer["mainboard"].activate_variant("variant_1").register(name="MSI B550-A Pro AMD B550 So.AM4 Dual Channel DDR4 ATX Retail", price=118.0)
    computer["mainboard"].create_variant("variant_2")
    computer["mainboard"].activate_variant("variant_2").register(name="Gigabyte Z590 UD AC (Z590,S1200,ATX)", price=129.94)

    computer["gpu"].register(name="12GB MSI GeForce RTX 3060 Gaming X (Retail)", price=479.0)
    computer["gpu"].create_variant("variant_1")
    computer["gpu"].activate_variant("variant_1").register(name="12GB MSI GeForce RTX 3060 Ventus 3X OC (Retail)", price=469.0)
    computer["gpu"].create_variant("variant_2")
    computer["gpu"].activate_variant("variant_2").register(name="12GB MSI GeForce RTX 3060 Gaming Z Trio (LHR) Aktiv PCIe 4.0 x16)", price=482.0)

    computer["case"].register(name="case", price=70.0)

    computer["monitor"].register(name="LG UltraFine 4K", price=423.99)
    computer["monitor"].create_variant("variant_1")
    computer["monitor"].activate_variant("variant_1").register(name="31.5' (80,01cm) LG Electronics UltraWide 32BN67U-B schwarz 3840x2160 1x DisplayPort-Out 1.4 / 2xHDMI 2.0", price=469.0)

    computer["fan"].register(name="fan", price=40.0)

    # some_child = Node("child_2")
    # computer["psu"].attach(some_child)
    # computer["psu"].create_variant("variant_1")
    # computer["psu"].activate_variant("variant_1")
    # computer["psu"].gen_tree().inspect()
    # computer.create_variant("lolo")
    # computer = computer.activate_variant("lolo")

    # computer = computer.activate_variant("base")
    root_configurations = computer.gen_config()
    combinations = [ApexRegistry().handle_resolve(node[0]).list_variants() for node in root_configurations[0]]
    prices = []
    logger.setLevel("CRITICAL")
    SAFETY = 0
    for entry in list(product(*combinations)):
        price = 0
        for node in computer.gen_tree():
            node: Node
            for variant in entry:
                variant: Node
                if node.identity.name == variant.identity.name:
                    node.activate_variant(variant.get_variant_name())

        for node in computer.gen_tree():
            if "price" in node.data_registry.keys():
                price += node.data_registry["price"]
        computer.inspect()
        prices.append(price)
        SAFETY += 1
        if SAFETY == 3:
            break
    logger.setLevel("SPAM")
    prices.sort()
    logger.error(computer.estimate_configurations())
    # logger.error(min(prices))
    # logger.error(mean(prices))
    # logger.error(max(prices))

if __name__ == "__main__":
    logger.critical("#" * 15 + "-MAIN_START-" + "#" * 57)
    main()
    logger.critical("#" * 15 + "-MAIN_STOP-" + "#" * 58)
