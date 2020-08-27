import datetime
import threading
import time

import cv2
import numpy as np
import picamera
from picamera.array import PiRGBArray

from .detection import run_detection
from .system import System


class Record(threading.Thread):
    def __init__(self, camera):
        threading.Thread.__init__(self, name="record_thread")
        system = System()
        json_loads = system.json_loads()
        self._camera_cap = camera
        self._width = json_loads["record"]["width"]
        self._height = json_loads["record"]["height"]
        self._sec = "SECTRANS"
        self._company = json_loads["record"]["company"]
        self._car = json_loads["record"]["car"]
        self._camera = json_loads["record"]["cam_id"]
        self._cam_flip = json_loads["record"]["cam_flip"]
        self._video_path = json_loads["record"]["video_path"]
        self._video_name = json_loads["record"]["video_name"]
        self._framerate = json_loads["record"]["framerate"]
        self._duration = json_loads["record"]["duration"] + 1

    def video_capture(self):
        """Método responsável por realizar a captura de vídeos.
        """
        try:
            system = System()
            video_name = str(datetime.datetime.now().strftime(self._video_name))
            video_path = system.create_dir(self._video_path)
            video_output = f"{self._video_path}/{video_name}"
            width = self._width
            height = self._height
            framerate = self._framerate
            self._camera_cap.resolution = (width, height)
            self._camera_cap.framerate = framerate
            if self._cam_flip == 1:
                self._camera_cap.vflip = True
            else:
                self._camera_cap.vflip = False
            rawCapture = PiRGBArray(self._camera_cap, size=(width, height))
            time_start = time.time()

            # transforma o que é capturado em objeto opencv
            out = cv2.VideoWriter(
                video_output,
                cv2.VideoWriter_fourcc(*"mp4v"),
                framerate,
                (width, height),
            )

            while True:
                # Para cada frame capturado é inserido informações 
                for frame in self._camera_cap.capture_continuous(
                    rawCapture, format="bgr", use_video_port=False
                ):

                    image = frame.array

                    font = cv2.FONT_HERSHEY_SIMPLEX
                    sec = self._sec
                    date_time = str(
                        datetime.datetime.now().strftime("DIA: %d/%m/%Y - HORA: %T")
                    )
                    company = str(self._company).upper()
                    car = self._car
                    v_camera = self._camera
                    vehicle = f"CARRO: {car}({v_camera})"

                    # inseri tarja superior e inferior no vídeo além das informações
                    #  sobre de data e hora, nome da empresa e nome do cliente
                    image = img = cv2.rectangle(
                        image, (0, 0), (width, 20), (0, 0, 0), -1
                    )
                    image = img2 = cv2.rectangle(
                        image, (0, height + 30), (width, height - 20), (0, 0, 0), -1
                    )
                    image = cv2.putText(
                        image,
                        company,
                        (5, 15),
                        font,
                        0.4,
                        (0, 255, 255),
                        1,
                        cv2.LINE_AA,
                    )
                    image = cv2.putText(
                        image, sec, (380, 15), font, 0.4, (0, 255, 255), 1, cv2.LINE_AA
                    )
                    image = cv2.putText(
                        image,
                        vehicle,
                        (5, 251),
                        font,
                        0.4,
                        (0, 255, 255),
                        1,
                        cv2.LINE_AA,
                    )
                    image = cv2.putText(
                        image,
                        date_time,
                        (210, 251),
                        font,
                        0.4,
                        (0, 255, 255),
                        1,
                        cv2.LINE_AA,
                    )
                    out.write(image)

                    rawCapture.truncate(0)

                    # tempo de duração do vídeo
                    if (time.time() - time_start) >= self._duration:
                        print(f"Vídeo gravado em: {video_output}")
                        break

                else:
                    break

            self._camera_cap.close()
            out.release()
            cv2.destroyAllWindows()
        except AttributeError:
            pass
        except Exception as e:
            print(f"Erro record: {e}")

    def run(self):
        """[Sobrecarga do método run]

        To do: trocar print por log no sistema
        """
        while True:

            detection = run_detection(self._camera_cap)

            if detection == True:

                print("Iniciando Gravação")
                self.video_capture()
                print("Concluindo Gravação")
