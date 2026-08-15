from pathlib import Path
import shutil
import subprocess

import pytest

from hil.protocol import SensorFrame, encode_sensor_frame


def test_c_header_encodes_exact_same_sensor_frame_as_python(tmp_path: Path):
    gcc = shutil.which("gcc")
    if gcc is None:
        pytest.skip("host gcc is not installed")
    root = Path(__file__).resolve().parents[2]
    source = tmp_path / "check.c"
    source.write_text(r'''
#include <stdio.h>
#include "hil_protocol.h"
int main(void) {
    hil_sensor_frame_t f = {.sequence=0x1234, .bus_mv=12050, .current_ma=4321, .temperature_cc=7123, .flags=5};
    unsigned char raw[HIL_FRAME_SIZE];
    hil_encode_sensor_frame(&f, raw);
    for (unsigned i=0; i<HIL_FRAME_SIZE; ++i) printf("%02x", raw[i]);
    printf("\n%04x\n", hil_crc16_ccitt_false((const unsigned char*)"123456789", 9));
    return 0;
}
''')
    exe = tmp_path / "check"
    subprocess.run([gcc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(root / "firmware/common"), str(source), "-o", str(exe)], check=True)
    output = subprocess.check_output([str(exe)], text=True).splitlines()
    expected = encode_sensor_frame(SensorFrame(0x1234, 12050, 4321, 7123, 5)).hex()
    assert output == [expected, "29b1"]
