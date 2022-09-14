from typing import List

import numpy as np
from norfair import Detection

from soccer.ball import Ball
from soccer.draw import Draw
from soccer.team import Team


class Player:
    def __init__(self, detection: Detection):
        """

        Initialize Player

        Parameters
        ----------
        detection : Detection
            Detection containing the player
        """
        self.detection = detection

        self.team = None

        if detection:
            if "team" in detection.data:
                self.team = detection.data["team"]

    @property
    def left_foot(self):
        points = self.detection.points

        x1, y1 = points[0]
        x2, y2 = points[1]

        return [x1, y2]

    @property
    def right_foot(self):
        return self.detection.points[1]

    @property
    def feet(self) -> np.ndarray:
        return np.array([self.left_foot, self.right_foot])

    def distance_to_ball(self, ball: Ball) -> float:
        """
        Returns the distance between the player closest foot and the ball

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

        left_foot_distance = np.linalg.norm(ball.center - self.left_foot)
        right_foot_distance = np.linalg.norm(ball.center - self.right_foot)

        return min(left_foot_distance, right_foot_distance)

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

    def draw(
        self, frame: np.ndarray, confidence: bool = False, id: bool = False
    ) -> np.ndarray:
        """
        Draw the player on the frame

        Parameters
        ----------
        frame : np.ndarray
            Frame to draw on
        confidence : bool, optional
            Whether to draw confidence text in bounding box, by default False
        id : bool, optional
            Whether to draw id text in bounding box, by default False

        Returns
        -------
        np.ndarray
            Frame with player drawn
        """
        if self.detection is None:
            return frame

        if self.team is not None:
            self.detection.data["color"] = self.team.color

        return Draw.draw_detection(self.detection, frame, condifence=confidence, id=id)

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

        return Draw.draw_pointer(detection=self.detection, img=frame, color=color)

    def __str__(self):
        return f"Player: {self.feet}, team: {self.team}"

    @staticmethod
    def draw_players(
        players: List["Player"],
        frame: np.ndarray,
        confidence: bool = False,
        id: bool = False,
    ) -> np.ndarray:
        """
        Draw all players on the frame

        Parameters
        ----------
        players : List[Player]
            List of Player objects
        frame : np.ndarray
            Frame to draw on
        confidence : bool, optional
            Whether to draw confidence text in bounding box, by default False
        id : bool, optional
            Whether to draw id text in bounding box, by default False

        Returns
        -------
        np.ndarray
            Frame with players drawn
        """
        for player in players:
            frame = player.draw(frame, confidence=confidence, id=id)

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
                team = Team.from_name(teams=teams, name=team_name)
                detection.data["team"] = team

            player = Player(detection=detection)

            players.append(player)

        return players