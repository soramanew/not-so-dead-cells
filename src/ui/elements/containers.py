from util.type import Vec2

from .base import Panel, UIElement


class Grid(Panel):
    def __init__(
        self,
        relative_pos: Vec2,
        children: list[list[UIElement]] = None,
        vertical: bool = False,
        gaps: Vec2 = (0, 0),
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        self.children: list[Panel] = []
        if children:
            for i, section in enumerate(children):
                if i > 0:
                    if vertical:
                        row_anchors = {"left": "right", "left_target": self.children[i - 1]}
                        row_gaps = gaps[0], 0
                    else:
                        row_anchors = {"top": "bottom", "top_target": self.children[i - 1]}
                        row_gaps = 0, gaps[1]
                else:
                    row_anchors = None
                    row_gaps = 0, 0
                row = Panel(row_gaps, (0, 0), container=self, anchors=row_anchors)

                for j, child in enumerate(section):
                    if j > 0:
                        if vertical:
                            cell_anchors = {"top": "bottom", "top_target": row.children[j - 1]}
                            cell_gaps = 0, gaps[1]
                        else:
                            cell_anchors = {"left": "right", "left_target": row.children[j - 1]}
                            cell_gaps = gaps[0], 0
                    else:
                        cell_anchors = None
                        cell_gaps = 0, 0
                    cell = Panel(cell_gaps, (0, 0), container=row, anchors=cell_anchors)
                    child.set_container(cell)

        self.vertical: bool = vertical
        self.gaps: Vec2 = gaps

        super().__init__(relative_pos, (0, 0), container=container, anchors=anchors)

    def add_child(self, child: Panel) -> None:
        # Grids are not supposed to be changed, this is for when adding the children on init
        self.children.append(child)

    def remove_child(self, child: UIElement) -> None:
        raise NotImplementedError(f"Unable to remove children from {repr(self)}")

    def update_size(self) -> None:
        # Pack all panel children sizes to fit
        self.pack(2)

        # Get max cell size
        cell_width = max(cell.width for row in self.children for cell in row.children)
        cell_height = max(cell.height for row in self.children for cell in row.children)

        # Set all cell sizes to max cell size (so all are equal)
        for row in self.children:
            for cell in row.children:
                cell.size = cell_width, cell_height

        # Calculate new size based on cell size
        if self.vertical:
            self.width = (cell_width + self.gaps[0]) * len(self.children)
            self.height = (cell_height + self.gaps[1]) * max(len(col.children) for col in self.children)
        else:
            self.width = (cell_width + self.gaps[0]) * max(len(col.children) for col in self.children)
            self.height = (cell_height + self.gaps[1]) * len(self.children)

        # Update position after to make children positions correct
        self.update_position()

    def update(self) -> None:
        if not self.dirty:
            return

        super().update()
        self.update_size()
