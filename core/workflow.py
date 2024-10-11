class WorkflowNode:
    def __init__(self, screenshot_id, start_time, end_time, video_url, action_summary, next_screenshot_id=None):
        self.screenshot_id = screenshot_id
        self.start_time = start_time
        self.end_time = end_time
        self.video_url = video_url
        self.action_summary = action_summary
        self.next_screenshot_id = next_screenshot_id

class Workflow:
    def __init__(self):
        self.head = None
        self.nodes = []

    def add_node(self, screenshot_id, start_time, end_time, video_url, action_summary, next_screenshot_id=None):
        new_node = WorkflowNode(screenshot_id, start_time, end_time, video_url, action_summary, next_screenshot_id)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next_screenshot_id:
                current = current.next_screenshot_id
            current.next_screenshot_id = new_node.screenshot_id
        self.nodes.append(new_node)