from typing import List
import numpy as np
import PIL
from norfair import Detection
from game.ball import Ball
from game.team import Team
from annotations.draw import draw_detection_mask, draw_pointer
import supervision as sv


class Player:
    def __init__(self, detection: Detection):
        """

        Initialize Player

        Parameters
        ----------
        detection : Detection
            Detection containing the player
        """
        self.txy = None # transformed xy
        self.be_xy = None # birds eye view xy
        self.detection = detection
        self.in_possession = False
        self.team = None

        if detection:
            if "team" in detection.data:
                self.team = detection.data["team"]

    def get_left_foot(self, points: np.array):
        x1, y1 = points[0]
        x2, y2 = points[1]

        return [x1, y2]

    def get_right_foot(self, points: np.array):
        return points[1]

    def get_center(self, points: np.array):
        points = self.detection.points
        x1, y1 = points[0]
        x2, y2 = points[1]
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        center = np.array([center_x, center_y])
        return center

    def get_xy(self):
        points = self.detection.points
        x1, y1 = points[0]
        x2, y2 = points[1]
        x = (x1 + x2) / 2
        y = min(y1, y2)
        xy = np.array([x, y])
        return xy

    @property
    def xy(self):
        return self.get_xy()

    @property
    def left_foot(self):
        points = self.detection.points
        left_foot = self.get_left_foot(points)

        return left_foot

    @property
    def right_foot(self):
        points = self.detection.points
        right_foot = self.get_right_foot(points)

        return right_foot

    @property
    def center(self):
        points = self.detection.points
        center = self.get_center(points)
        return center

    @property
    def left_foot_abs(self):
        points = self.detection.absolute_points
        left_foot_abs = self.get_left_foot(points)

        return left_foot_abs

    @property
    def right_foot_abs(self):
        points = self.detection.absolute_points
        right_foot_abs = self.get_right_foot(points)

        return right_foot_abs

    @property
    def center_abs(self):
        points = self.detection.absolute_points
        center_abs = self.get_center(points)
        return center_abs

    @property
    def feet(self) -> np.ndarray:
        return np.array([self.left_foot, self.right_foot])

    def distance_to_ball(self, ball: Ball) -> float:
        """
        Returns the distance between the players center and the ball

        Parameters
        ----------
        ball : Ball
            Ball object

        Returns
        -------
        float
            Distance between the player closest foot and the ball
        """

        if self.detection is None or ball.center is None:
            return None

        center_distance = np.linalg.norm(ball.center - self.center)

        return center_distance

    def distance_to_last_ball(self, ball: Ball) -> float:
        """
        Returns the distance between the player closest foot and the most recent ball detection

        Parameters
        ----------
        ball : Ball
            Ball object

        Returns
        -------
        float
            Distance between the player closest foot and the most recent ball detection
        """

        if self.detection is None:
            return None

        if ball.center is None:
            if ball.last_detection is not None and ball.last_detection.center is not None:
                center_distance = np.linalg.norm(ball.last_detection.center - self.center)
                return center_distance
            else:
                return None

        center_distance = np.linalg.norm(ball.detection.center - self.center)
        return center_distance

    def closest_foot_to_ball(self, ball: Ball) -> np.ndarray:
        """

        Returns the closest foot to the ball

        Parameters
        ----------
        ball : Ball
            Ball object

        Returns
        -------
        np.ndarray
            Closest foot to the ball (x, y)
        """

        if self.detection is None or ball.center is None:
            return None

        left_foot_distance = np.linalg.norm(ball.center - self.left_foot)
        right_foot_distance = np.linalg.norm(ball.center - self.right_foot)

        if left_foot_distance < right_foot_distance:
            return self.left_foot

        return self.right_foot

    def closest_center_to_ball_abs(self, ball: Ball) -> np.ndarray:
        """

        Returns the closest center to the ball

        Parameters
        ----------
        ball : Ball
            Ball object

        Returns
        -------
        np.ndarray
            Closest foot to the ball (x, y)
        """

        if self.detection is None or ball.center_abs is None:
            return None

        center_distance = np.linalg.norm(ball.center_abs - self.center_abs)

        return self.center if center_distance <= self.distance_to_ball(ball) else None

    def closest_foot_to_ball_abs(self, ball: Ball) -> np.ndarray:
        """

        Returns the closest foot to the ball

        Parameters
        ----------
        ball : Ball
            Ball object

        Returns
        -------
        np.ndarray
            Closest foot to the ball (x, y)
        """

        if self.detection is None or ball.center_abs is None:
            return None

        left_foot_distance = np.linalg.norm(ball.center_abs - self.left_foot_abs)
        right_foot_distance = np.linalg.norm(ball.center_abs - self.right_foot_abs)

        if left_foot_distance < right_foot_distance:
            return self.left_foot_abs

        return self.right_foot_abs

    def draw(
        self, frame: PIL.Image.Image, confidence: bool = False, id: bool = False, txy: bool = False
    ) -> PIL.Image.Image:
        """
        Draw the player on the frame

        Parameters
        ----------
        frame : PIL.Image.Image
            Frame to draw on
        confidence : bool, optional
            Whether to draw confidence text in bounding box, by default False
        id : bool, optional
            Whether to draw id text in bounding box, by default False

        Returns
        -------
        PIL.Image.Image
            Frame with player drawn
        """
        if self.detection is None:
            return frame

        if self.team is not None:
            self.detection.data["color"] = self.team.color
            # print('i')
            # print(self.detection.data)
        mask_annotator = sv.MaskAnnotator(color=self.detection.data["color"], opacity=0.5)
        sv_detections=sv.Detections(xyxy=self.detection.points,
                                    mask=self.detection.data["mask"],
                                    tracker_id=self.detection.data["txy"],)
        annotated_frame = mask_annotator.annotate(
            scene=frame,
            detections=sv_detections,
        )

        return annotated_frame

    def draw_pointer(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw a pointer above the player

        Parameters
        ----------
        frame : np.ndarray
            Frame to draw on

        Returns
        -------
        np.ndarray
            Frame with pointer drawn
        """
        if self.detection is None:
            return frame

        color = None

        if self.team:
            color = self.team.color

        return draw_pointer(detection=self.detection, img=frame, color=color)

    def __str__(self):
        return f"Player: {self.feet}, team: {self.team}"

    def __eq__(self, other: "Player") -> bool:
        if isinstance(self, Player) == False or isinstance(other, Player) == False:
            return False

        self_id = self.detection.data["id"]
        other_id = other.detection.data["id"]

        return self_id == other_id

    @staticmethod
    def have_same_id(player1: "Player", player2: "Player") -> bool:
        """
        Check if player1 and player2 have the same ids

        Parameters
        ----------
        player1 : Player
            One player
        player2 : Player
            Another player

        Returns
        -------
        bool
            True if they have the same id
        """
        if not player1 or not player2:
            return False
        if "id" not in player1.detection.data or "id" not in player2.detection.data:
            return False
        return player1 == player2

    @staticmethod
    def draw_players(
        players: List["Player"],
        frame: PIL.Image.Image,
        confidence: bool = False,
        id: bool = False,
        txy: bool = True,
    ) -> PIL.Image.Image:
        """
        Draw all players on the frame

        Parameters
        ----------
        players : List[Player]
            List of Player objects
        frame : PIL.Image.Image
            Frame to draw on
        confidence : bool, optional
            Whether to draw confidence text in bounding box, by default False
        id : bool, optional
            Whether to draw id text in bounding box, by default False

        Returns
        -------
        PIL.Image.Image
            Frame with players drawn
        """
        if players:
            for player in players:
                frame = player.draw(frame, confidence=confidence, id=id, txy=txy)

        return frame

    @staticmethod
    def from_detections(
        detections: List[Detection], teams=List[Team]
    ) -> List["Player"]:
        """
        Create a list of Player objects from a list of detections and a list of teams.

        It reads the classification string field of the detection, converts it to a
        Team object and assigns it to the player.

        Parameters
        ----------
        detections : List[Detection]
            List of detections
        teams : List[Team], optional
            List of teams, by default List[Team]

        Returns
        -------
        List[Player]
            List of Player objects
        """
        players = []

        for detection in detections:
            if detection is None:
                continue

            if "classification" in detection.data:
                team_name = detection.data["classification"]
                # print(team_name)
                team = Team.from_name(teams=teams, name=team_name)
                detection.data["team"] = team
                # print(detection.data)

            player = Player(detection=detection)

            players.append(player)

        return players
