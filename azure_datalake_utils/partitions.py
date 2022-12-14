"""Utilidades para particiones."""
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import itertools
import logging

from typing import Any, Dict, List, Tuple
from adlfs import AzureBlobFileSystem


class HivePartitiion:
    """Clase para tratar con la particiones tipo hive.

    Una partición tipo hive son archivos que son almacenados de la forma
    /ruta/to/archivo/particion_1=1/particion2=2/archivo_con_info.extension Esta
    Clase ayuda a descubrir los archivos que se quieren leer y poder cargar
    las columnas como particiones.

    Tambien incluye una opción para filtrar las particiones que se quieren cargar,
    tambien se puede forzar a incluir una partición especifica.

    Otra opción tambien puede ser usada para leer el archivo mas reciente en el ultimo nivel de
    la partición.

    **NOTA**: solo descubre un arhivo por carperta, es decir, si hay multiples archivos
    en el nivel más bajo, solo garantiza leer uno solo.

    Args:
        ruta: ruta donde se encuentran los archivos almancenados.

    Attributes:
        ruta: atributo con la ruta a descubir.
        partition_cols: dict con las particiones a leer de manera especifica.
            Al pasar esta opción implica que noy descubrimiento.
        partition_filter: diccionarios con valores a filtrar en la partición
        last_modidfied_deeper_level: si se debe filtrar para obtener el mas reciente
            en el nivel más profundo.
    """

    def __init__(
        self,
        ruta: str,
        partition_cols: Dict[str, Any],
        partition_filter: Dict[str, Any] = {},
        last_modified_deeper_level: bool = False,
        fs: AzureBlobFileSystem = None,
    ) -> None:
        """Constructor."""
        self.ruta = ruta
        self.partition_files: List[Tuple[str, Dict[str, str]]] = [{}]
        self.partition_cols = partition_cols
        self.partition_filter = partition_filter
        self.last_modified_deeper_level = last_modified_deeper_level

        self.fs = fs
        self._discover()

    def _discover(self) -> None:
        """Metodo para descubrir las paritciones."""
        if self.partition_cols is not None:
            self._make_partitions_using_partition_cols()

    def _make_partitions_using_partition_cols(self) -> None:
        """Metodo para constuir particiones con la partition_cols y asi evitar descubrirlas."""
        combinations = itertools.product(*(self.partition_cols[name] for name in self.partition_cols))

        partitions = []
        for combination in combinations:
            part = {k: v for k, v in zip(self.partition_cols.keys(), combination)}
            partition_path = "/".join([f"{k}={v}" for k, v in part.items()])
            try:
                details = self.fs.listdir(f"{self.ruta}{partition_path}/")
                if len(details) > 0:
                    file_name = details[0]['name'].split("/")[-1]
                    partitions.append((file_name, part))
            except FileNotFoundError:
                logging.debug(f"{part} No tiene archivos")
                continue

        self.partition_files = partitions
