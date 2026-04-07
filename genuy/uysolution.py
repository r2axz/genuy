from itertools import accumulate, chain

from datetime import datetime

from mininec.mininec import c as speed_of_light
from mininec.mininec import Geo_Container, Wire
from mininec.mininec import Mininec, Excitation, Angle

class UYSolution(list):

    _FARFIELD_THETA = Angle(90, 0, 1)
    _FARFIELD_PHI = Angle(0, 5, 36)

    def __init__(self, iterable, *, element_radius):
        super().__init__(iterable)
        if len(self) % 2 == 0:
            raise ValueError("The length of the solution must be odd.")
        self.element_radius = element_radius

    @property
    def num_elements(self):
        return len(self) // 2 + 1
    
    @property
    def elements(self):
        return self[::2]
    
    @property
    def spacings(self):
        return self[1::2]

    @property
    def elements_at_positions(self):
        return zip(
            self.elements,
            accumulate(chain([0], self.spacings))
        )

    @property
    def boom_length(self):
        return sum(self.spacings)

    def _wavelength(self, frequency):
        return speed_of_light / (frequency * 1e6)

    def _create_geometry(self, frequency, nseg):
        wl = self._wavelength(frequency)
        taper_min = self.element_radius * 5.0
        taper_max = wl / nseg
        geo = Geo_Container()
        for i, (l, p) in enumerate(self.elements_at_positions):
            el = wl * l
            ep = wl * p
            wire = Wire(nseg, ep, -el/2 , 0, ep, el/2, 0, self.element_radius, i+1)
            wire.segtype = 3
            wire.taper_min = taper_min
            wire.taper_max = taper_max
            geo.append(wire)
        geo.compute_tags()
        return geo
    
    def simulate(self, frequency, *, nseg):
        geo = self._create_geometry(frequency, nseg)
        mininec = Mininec(frequency, geo, media=None)
        excitation = Excitation(cvolt = 1.0)
        mininec.register_source(excitation, pulse = nseg//2 - 1, geo_tag = 2)
        mininec.compute()
        mininec.compute_far_field(self._FARFIELD_THETA, self._FARFIELD_PHI)
        self.mininec = mininec
    
    @property
    def impedance(self):
        return self.mininec.sources[0].impedance

    def vswr(self, reference_impedance=50.0+0j):
        impedance = self.impedance
        abs_gamma = abs((impedance - reference_impedance) / (impedance + reference_impedance))
        return (1 + abs_gamma) / (1 - abs_gamma)
    
    @property
    def gain(self):
        return self.mininec.far_field.gain[0][0][1]

    @property
    def fb(self):
        return self.mininec.far_field.gain[0][0][1] - max(self.mininec.far_field.gain[0][i][1] for i in range(23, 36))

    def save_to_maa(self, filename, *, frequency=14.5, dm1=800, dm2=80, sc=2.0, ec=2):
        name = f'UY-{self.num_elements}el-{frequency}MHz'
        wl = self._wavelength(frequency)
        with open(filename, 'w') as f:
            f.write(f'{name}\n')
            f.write(f'*\n{frequency}\n')
            f.write(f'***Wires***\n{self.num_elements}\n')
            for (l, p) in self.elements_at_positions:
                el = wl * l
                ep = wl * p
                f.write(f'{ep:.6f},\t{-el/2:.6f},\t0.0,\t{ep:.6f},\t{el/2:.6f},\t0.0,\t{self.element_radius},\t-1\n')
            f.write(f'***Source***\n1,\t1\nw2c,\t0.0,\t1.0\n')
            f.write(f'***Load***\n0,\t1\n')
            f.write(f'***Segmentation***\n{dm1},\t{dm2},\t{sc:1f},\t{ec}\n')
            f.write(f'***G/H/M/R/AzEl/X***\n0,\t0.0,\t0,\t50.0,\t120,\t0,\t0.0\n')
            f.write(f'###Comment###\nCreated by genuy at {datetime.today().strftime("%Y-%m-%d %H:%M:%S")}\n')
