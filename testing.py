import yaml

from byteflow2 import (ControlLabel, BasicBlock, BlockMap, ByteFlowRenderer,
                       ByteFlow, ControlLabelGenerator,
                       loop_rotate)

from unittest import TestCase, main


def from_yaml(yaml_string):
    # Convert to BlockMap
    data = yaml.safe_load(yaml_string)
    block_map_graph = {}
    clg = ControlLabelGenerator()
    for index, jump_targets in data.items():
        begin_label = ControlLabel(str(clg.new_index()))
        end_label = ControlLabel("end")
        block = BasicBlock(
            begin_label,
            end_label,
            fallthrough=len(jump_targets["jt"]) == 1,
            backedges=set(),
            jump_targets=set((ControlLabel(i) for i in jump_targets["jt"])),
            name=None
        )
        block_map_graph[begin_label] = block
    return BlockMap(block_map_graph, clg=clg)


class BlockMapTestCase(TestCase):
    def assertEqualMaps(self, first_map, second_map):
        self.assertEqual(first_map.clg.index, second_map.clg.index)
        
        for _label in first_map.graph:
            self.assertEqual(first_map.graph[_label].begin, 
                             second_map.graph[_label].begin)
            self.assertEqual(first_map.graph[_label].end, 
                             second_map.graph[_label].end)
            self.assertEqual(first_map.graph[_label].jump_targets,
                             second_map.graph[_label].jump_targets)


class TestJoinReturns(BlockMapTestCase):

    def test_two_returns(self):
        original = """
        "0":
            jt: ["1", "2"]
        "1":
            jt: []
        "2":
            jt: []
        """
        original_block_map = from_yaml(original)
        expected = """
        "0":
            jt: ["1", "2"]
        "1":
            jt: ["3"]
        "2":
            jt: ["3"]
        "3":
            jt: []
        """
        expected_block_map = from_yaml(expected)
        original_block_map.join_returns()
        self.assertEqualMaps(expected_block_map, original_block_map)


class TestJoinTailsAndExits(BlockMapTestCase):

    def test_join_tails_and_exits_case_00(self):
        original = """
        "0":
            jt: ["1"]
        "1":
            jt: []
        """
        original_block_map = from_yaml(original)
        expected = """
        "0":
            jt: ["1"]
        "1":
            jt: []
        """
        expected_block_map = from_yaml(expected)

        tails = {ControlLabel(i) for i in ("0")}
        exits = {ControlLabel(i) for i in ("1")}
        solo_tail_label, solo_exit_label = original_block_map.join_tails_and_exits(tails, exits)

        self.assertEqualMaps(expected_block_map, original_block_map)
        self.assertEqual(ControlLabel("0"), solo_tail_label)
        self.assertEqual(ControlLabel("1"), solo_exit_label)

    def test_join_tails_and_exits_case_01(self):
        original = """
        "0":
            jt: ["1", "2"]
        "1":
            jt: ["3"]
        "2":
            jt: ["3"]
        "3":
            jt: []
        """
        original_block_map = from_yaml(original)
        expected = """
        "0":
            jt: ["4"]
        "1":
            jt: ["3"]
        "2":
            jt: ["3"]
        "3":
            jt: []
        "4":
            jt: ["1", "2"]
        """
        expected_block_map = from_yaml(expected)

        tails = {ControlLabel(i) for i in ("0")}
        exits = {ControlLabel(i) for i in ("1", "2")}
        solo_tail_label, solo_exit_label = original_block_map.join_tails_and_exits(tails, exits)

        self.assertEqualMaps(expected_block_map, original_block_map)
        self.assertEqual(ControlLabel("0"), solo_tail_label)
        self.assertEqual(ControlLabel("4"), solo_exit_label)

    def test_join_tails_and_exits_case_02_01(self):
        original = """
        "0":
            jt: ["1", "2"]
        "1":
            jt: ["3"]
        "2":
            jt: ["3"]
        "3":
            jt: []
        """
        original_block_map = from_yaml(original)
        expected = """
        "0":
            jt: ["1", "2"]
        "1":
            jt: ["4"]
        "2":
            jt: ["4"]
        "3":
            jt: []
        "4":
            jt: ["3"]
        """
        expected_block_map = from_yaml(expected)

        tails = {ControlLabel(i) for i in ("1", "2")}
        exits = {ControlLabel(i) for i in ("3")}
        solo_tail_label, solo_exit_label = original_block_map.join_tails_and_exits(tails, exits)

        self.assertEqualMaps(expected_block_map, original_block_map)
        self.assertEqual(ControlLabel("4"), solo_tail_label)
        self.assertEqual(ControlLabel("3"), solo_exit_label)

    def test_join_tails_and_exits_case_02_02(self):
        original = """
        "0":
            jt: ["1", "2"]
        "1":
            jt: ["3"]
        "2":
            jt: ["1", "3"]
        "3":
            jt: []
        """
        original_block_map = from_yaml(original)
        expected = """
        "0":
            jt: ["1", "2"]
        "1":
            jt: ["4"]
        "2":
            jt: ["1", "4"]
        "3":
            jt: []
        "4":
            jt: ["3"]
        """
        expected_block_map = from_yaml(expected)

        tails = {ControlLabel(i) for i in ("1", "2")}
        exits = {ControlLabel(i) for i in ("3")}
        ByteFlowRenderer().render_byteflow(ByteFlow({},
                                                    original_block_map)).view("before")
        solo_tail_label, solo_exit_label = original_block_map.join_tails_and_exits(tails, exits)
        self.assertEqualMaps(expected_block_map, original_block_map)
        self.assertEqual(ControlLabel("4"), solo_tail_label)
        self.assertEqual(ControlLabel("3"), solo_exit_label)

    def test_join_tails_and_exits_case_03_01(self):

        original = """
        "0":
            jt: ["1", "2"]
        "1":
            jt: ["3"]
        "2":
            jt: ["4"]
        "3":
            jt: ["5"]
        "4":
            jt: ["5"]
        "5":
            jt: []
        """
        original_block_map = from_yaml(original)
        expected = """
        "0":
            jt: ["1", "2"]
        "1":
            jt: ["6"]
        "2":
            jt: ["6"]
        "3":
            jt: ["5"]
        "4":
            jt: ["5"]
        "5":
            jt: []
        "6":
            jt: ["7"]
        "7":
            jt: ["3", "4"]
        """
        expected_block_map = from_yaml(expected)

        tails = {ControlLabel(i) for i in ("1", "2")}
        exits = {ControlLabel(i) for i in ("3", "4")}
        solo_tail_label, solo_exit_label = original_block_map.join_tails_and_exits(tails, exits)
        self.assertEqualMaps(expected_block_map, original_block_map)
        self.assertEqual(ControlLabel("6"), solo_tail_label)
        self.assertEqual(ControlLabel("7"), solo_exit_label)

    def test_join_tails_and_exits_case_03_02(self):

        original = """
        "0":
            jt: ["1", "2"]
        "1":
            jt: ["3"]
        "2":
            jt: ["1", "4"]
        "3":
            jt: ["5"]
        "4":
            jt: ["5"]
        "5":
            jt: []
        """
        original_block_map = from_yaml(original)
        expected = """
        "0":
            jt: ["1", "2"]
        "1":
            jt: ["6"]
        "2":
            jt: ["1", "6"]
        "3":
            jt: ["5"]
        "4":
            jt: ["5"]
        "5":
            jt: []
        "6":
            jt: ["7"]
        "7":
            jt: ["3", "4"]
        """
        expected_block_map = from_yaml(expected)
        tails = {ControlLabel(i) for i in ("1", "2")}
        exits = {ControlLabel(i) for i in ("3", "4")}
        solo_tail_label, solo_exit_label = original_block_map.join_tails_and_exits(tails, exits)
        self.assertEqualMaps(expected_block_map, original_block_map)
        self.assertEqual(ControlLabel("6"), solo_tail_label)
        self.assertEqual(ControlLabel("7"), solo_exit_label)


class TestLoopRotate(TestCase):

    def test_basic_for_loop(self):

        original = """
        "0":
            jt: ["1"]
        "1":
            jt: ["2", "3"]
        "2":
            jt: ["1"]
        "3":
            jt: []
        """
        original_block_map = from_yaml(original)
        expected = """
        "0":
            jt: []
        """
        expected_block_map = from_yaml(expected)

        ByteFlowRenderer().render_byteflow(ByteFlow({}, original_block_map)).view("before")
        loop_rotate(original_block_map, {ControlLabel("1"), ControlLabel("2")})
        print(original_block_map.compute_scc())
        ByteFlowRenderer().render_byteflow(ByteFlow({}, original_block_map)).view("original")
        ByteFlowRenderer().render_byteflow(ByteFlow({}, expected_block_map)).view("expected")
        self.assertEqualMaps(expected_block_map, original_block_map)

if __name__ == '__main__':
    main()
