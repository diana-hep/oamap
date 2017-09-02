#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
import tempfile
import unittest

from plur.util.diskcache import DiskCache

def lstree(base, path=""):
    for item in sorted(os.listdir(os.path.join(base, path))):
        if os.path.isdir(os.path.join(base, path, item)):
            if item != "config":
                yield os.path.join(path, item) + os.sep
                for x in lstree(base, os.path.join(path, item)):
                    yield x
        else:
            yield os.path.join(path, item)

class TestDiskCache(unittest.TestCase):
    def runTest(self):
        pass
    
    def test_directory_structure(self):
        filling = [
            ["0.a.None"],
            ["0.a.None", "1.b.None"],
            ["0.a.None", "1.b.None", "2.c.None"],
            ["0/", "0/0.a.None", "0/1.b.None", "0/2.c.None", "1/", "1/0.d.None"],
            ["0/", "0/0.a.None", "0/1.b.None", "0/2.c.None", "1/", "1/0.d.None", "1/1.e.None"],
            ["0/", "0/0.a.None", "0/1.b.None", "0/2.c.None", "1/", "1/0.d.None", "1/1.e.None", "1/2.f.None"],
            ["0/", "0/0.a.None", "0/1.b.None", "0/2.c.None", "1/", "1/0.d.None", "1/1.e.None", "1/2.f.None", "2/", "2/0.g.None"],
            ["0/", "0/0.a.None", "0/1.b.None", "0/2.c.None", "1/", "1/0.d.None", "1/1.e.None", "1/2.f.None", "2/", "2/0.g.None", "2/1.h.None"],
            ["0/", "0/0.a.None", "0/1.b.None", "0/2.c.None", "1/", "1/0.d.None", "1/1.e.None", "1/2.f.None", "2/", "2/0.g.None", "2/1.h.None", "2/2.i.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None", "1/1/", "1/1/0.m.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None", "1/1/", "1/1/0.m.None", "1/1/1.n.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None", "1/1/", "1/1/0.m.None", "1/1/1.n.None", "1/1/2.o.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None", "1/1/", "1/1/0.m.None", "1/1/1.n.None", "1/1/2.o.None", "1/2/", "1/2/0.p.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None", "1/1/", "1/1/0.m.None", "1/1/1.n.None", "1/1/2.o.None", "1/2/", "1/2/0.p.None", "1/2/1.q.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None", "1/1/", "1/1/0.m.None", "1/1/1.n.None", "1/1/2.o.None", "1/2/", "1/2/0.p.None", "1/2/1.q.None", "1/2/2.r.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None", "1/1/", "1/1/0.m.None", "1/1/1.n.None", "1/1/2.o.None", "1/2/", "1/2/0.p.None", "1/2/1.q.None", "1/2/2.r.None", "2/", "2/0/", "2/0/0.s.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None", "1/1/", "1/1/0.m.None", "1/1/1.n.None", "1/1/2.o.None", "1/2/", "1/2/0.p.None", "1/2/1.q.None", "1/2/2.r.None", "2/", "2/0/", "2/0/0.s.None", "2/0/1.t.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None", "1/1/", "1/1/0.m.None", "1/1/1.n.None", "1/1/2.o.None", "1/2/", "1/2/0.p.None", "1/2/1.q.None", "1/2/2.r.None", "2/", "2/0/", "2/0/0.s.None", "2/0/1.t.None", "2/0/2.u.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None", "1/1/", "1/1/0.m.None", "1/1/1.n.None", "1/1/2.o.None", "1/2/", "1/2/0.p.None", "1/2/1.q.None", "1/2/2.r.None", "2/", "2/0/", "2/0/0.s.None", "2/0/1.t.None", "2/0/2.u.None", "2/1/", "2/1/0.v.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None", "1/1/", "1/1/0.m.None", "1/1/1.n.None", "1/1/2.o.None", "1/2/", "1/2/0.p.None", "1/2/1.q.None", "1/2/2.r.None", "2/", "2/0/", "2/0/0.s.None", "2/0/1.t.None", "2/0/2.u.None", "2/1/", "2/1/0.v.None", "2/1/1.w.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None", "1/1/", "1/1/0.m.None", "1/1/1.n.None", "1/1/2.o.None", "1/2/", "1/2/0.p.None", "1/2/1.q.None", "1/2/2.r.None", "2/", "2/0/", "2/0/0.s.None", "2/0/1.t.None", "2/0/2.u.None", "2/1/", "2/1/0.v.None", "2/1/1.w.None", "2/1/2.x.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None", "1/1/", "1/1/0.m.None", "1/1/1.n.None", "1/1/2.o.None", "1/2/", "1/2/0.p.None", "1/2/1.q.None", "1/2/2.r.None", "2/", "2/0/", "2/0/0.s.None", "2/0/1.t.None", "2/0/2.u.None", "2/1/", "2/1/0.v.None", "2/1/1.w.None", "2/1/2.x.None", "2/2/", "2/2/0.y.None"],
            ["0/", "0/0/", "0/0/0.a.None", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None", "1/1/", "1/1/0.m.None", "1/1/1.n.None", "1/1/2.o.None", "1/2/", "1/2/0.p.None", "1/2/1.q.None", "1/2/2.r.None", "2/", "2/0/", "2/0/0.s.None", "2/0/1.t.None", "2/0/2.u.None", "2/1/", "2/1/0.v.None", "2/1/1.w.None", "2/1/2.x.None", "2/2/", "2/2/0.y.None", "2/2/1.z.None"],
        ]

        touching = [
            ["0/", "0/0/", "0/0/1.b.None", "0/0/2.c.None", "0/1/", "0/1/0.d.None", "0/1/1.e.None", "0/1/2.f.None", "0/2/", "0/2/0.g.None", "0/2/1.h.None", "0/2/2.i.None", "1/", "1/0/", "1/0/0.j.None", "1/0/1.k.None", "1/0/2.l.None", "1/1/", "1/1/0.m.None", "1/1/1.n.None", "1/1/2.o.None", "1/2/", "1/2/0.p.None", "1/2/1.q.None", "1/2/2.r.None", "2/", "2/0/", "2/0/0.s.None", "2/0/1.t.None", "2/0/2.u.None", "2/1/", "2/1/0.v.None", "2/1/1.w.None", "2/1/2.x.None", "2/2/", "2/2/0.y.None", "2/2/1.z.None", "2/2/2.a.None"],
            ["0/", "0/0/", "0/0/0/", "0/0/0/1.b.None", "0/0/1/", "0/0/1/0.d.None", "0/0/1/1.e.None", "0/0/1/2.f.None", "0/0/2/", "0/0/2/0.g.None", "0/0/2/1.h.None", "0/0/2/2.i.None", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/1.k.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/0.m.None", "0/1/1/1.n.None", "0/1/1/2.o.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/1.q.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/0.s.None", "0/2/0/1.t.None", "0/2/0/2.u.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/1.w.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/0.y.None", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None"],
            ["0/", "0/0/", "0/0/0/", "0/0/0/1.b.None", "0/0/1/", "0/0/1/0.d.None", "0/0/1/2.f.None", "0/0/2/", "0/0/2/0.g.None", "0/0/2/1.h.None", "0/0/2/2.i.None", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/1.k.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/0.m.None", "0/1/1/1.n.None", "0/1/1/2.o.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/1.q.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/0.s.None", "0/2/0/1.t.None", "0/2/0/2.u.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/1.w.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/0.y.None", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None"],
            ["0/", "0/0/", "0/0/0/", "0/0/0/1.b.None", "0/0/1/", "0/0/1/0.d.None", "0/0/1/2.f.None", "0/0/2/", "0/0/2/1.h.None", "0/0/2/2.i.None", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/1.k.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/0.m.None", "0/1/1/1.n.None", "0/1/1/2.o.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/1.q.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/0.s.None", "0/2/0/1.t.None", "0/2/0/2.u.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/1.w.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/0.y.None", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None"],
            ["0/", "0/0/", "0/0/0/", "0/0/0/1.b.None", "0/0/1/", "0/0/1/0.d.None", "0/0/1/2.f.None", "0/0/2/", "0/0/2/1.h.None", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/1.k.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/0.m.None", "0/1/1/1.n.None", "0/1/1/2.o.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/1.q.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/0.s.None", "0/2/0/1.t.None", "0/2/0/2.u.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/1.w.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/0.y.None", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None"],
            ["0/", "0/0/", "0/0/0/", "0/0/0/1.b.None", "0/0/1/", "0/0/1/0.d.None", "0/0/1/2.f.None", "0/0/2/", "0/0/2/1.h.None", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/0.m.None", "0/1/1/1.n.None", "0/1/1/2.o.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/1.q.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/0.s.None", "0/2/0/1.t.None", "0/2/0/2.u.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/1.w.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/0.y.None", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None"],
            ["0/", "0/0/", "0/0/0/", "0/0/0/1.b.None", "0/0/1/", "0/0/1/0.d.None", "0/0/1/2.f.None", "0/0/2/", "0/0/2/1.h.None", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/1.n.None", "0/1/1/2.o.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/1.q.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/0.s.None", "0/2/0/1.t.None", "0/2/0/2.u.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/1.w.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/0.y.None", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None"],
            ["0/", "0/0/", "0/0/0/", "0/0/0/1.b.None", "0/0/1/", "0/0/1/0.d.None", "0/0/1/2.f.None", "0/0/2/", "0/0/2/1.h.None", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/1.n.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/1.q.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/0.s.None", "0/2/0/1.t.None", "0/2/0/2.u.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/1.w.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/0.y.None", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None"],
            ["0/", "0/0/", "0/0/0/", "0/0/0/1.b.None", "0/0/1/", "0/0/1/0.d.None", "0/0/1/2.f.None", "0/0/2/", "0/0/2/1.h.None", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/1.n.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/0.s.None", "0/2/0/1.t.None", "0/2/0/2.u.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/1.w.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/0.y.None", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None"],
            ["0/", "0/0/", "0/0/0/", "0/0/0/1.b.None", "0/0/1/", "0/0/1/0.d.None", "0/0/1/2.f.None", "0/0/2/", "0/0/2/1.h.None", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/1.n.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/1.t.None", "0/2/0/2.u.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/1.w.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/0.y.None", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None"],
            ["0/", "0/0/", "0/0/0/", "0/0/0/1.b.None", "0/0/1/", "0/0/1/0.d.None", "0/0/1/2.f.None", "0/0/2/", "0/0/2/1.h.None", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/1.n.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/1.t.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/1.w.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/0.y.None", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None"],
            ["0/", "0/0/", "0/0/0/", "0/0/0/1.b.None", "0/0/1/", "0/0/1/0.d.None", "0/0/1/2.f.None", "0/0/2/", "0/0/2/1.h.None", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/1.n.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/1.t.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/0.y.None", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None"],
            ["0/", "0/0/", "0/0/0/", "0/0/0/1.b.None", "0/0/1/", "0/0/1/0.d.None", "0/0/1/2.f.None", "0/0/2/", "0/0/2/1.h.None", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/1.n.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/1.t.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None"],
            ["0/", "0/0/", "0/0/1/", "0/0/1/0.d.None", "0/0/1/2.f.None", "0/0/2/", "0/0/2/1.h.None", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/1.n.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/1.t.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/1/1/", "1/1/1/0.b.None"],
            ["0/", "0/0/", "0/0/1/", "0/0/1/2.f.None", "0/0/2/", "0/0/2/1.h.None", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/1.n.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/1.t.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/1/1/", "1/1/1/0.b.None", "1/1/1/1.d.None"],
            ["0/", "0/0/", "0/0/2/", "0/0/2/1.h.None", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/1.n.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/1.t.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/1/1/", "1/1/1/0.b.None", "1/1/1/1.d.None", "1/1/1/2.f.None"],
            ["0/", "0/1/", "0/1/0/", "0/1/0/0.j.None", "0/1/0/2.l.None", "0/1/1/", "0/1/1/1.n.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/1.t.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/1/1/", "1/1/1/0.b.None", "1/1/1/1.d.None", "1/1/1/2.f.None", "1/1/2/", "1/1/2/0.h.None"],
            ["0/", "0/1/", "0/1/0/", "0/1/0/2.l.None", "0/1/1/", "0/1/1/1.n.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/1.t.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/1/1/", "1/1/1/0.b.None", "1/1/1/1.d.None", "1/1/1/2.f.None", "1/1/2/", "1/1/2/0.h.None", "1/1/2/1.j.None"],
            ["0/", "0/1/", "0/1/1/", "0/1/1/1.n.None", "0/1/2/", "0/1/2/0.p.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/1.t.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/1/1/", "1/1/1/0.b.None", "1/1/1/1.d.None", "1/1/1/2.f.None", "1/1/2/", "1/1/2/0.h.None", "1/1/2/1.j.None", "1/1/2/2.l.None"],
            ["0/", "0/1/", "0/1/2/", "0/1/2/0.p.None", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/1.t.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/1/1/", "1/1/1/0.b.None", "1/1/1/1.d.None", "1/1/1/2.f.None", "1/1/2/", "1/1/2/0.h.None", "1/1/2/1.j.None", "1/1/2/2.l.None", "1/2/", "1/2/0/", "1/2/0/0.n.None"],
            ["0/", "0/1/", "0/1/2/", "0/1/2/2.r.None", "0/2/", "0/2/0/", "0/2/0/1.t.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/1/1/", "1/1/1/0.b.None", "1/1/1/1.d.None", "1/1/1/2.f.None", "1/1/2/", "1/1/2/0.h.None", "1/1/2/1.j.None", "1/1/2/2.l.None", "1/2/", "1/2/0/", "1/2/0/0.n.None", "1/2/0/1.p.None"],
            ["0/", "0/2/", "0/2/0/", "0/2/0/1.t.None", "0/2/1/", "0/2/1/0.v.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/1/1/", "1/1/1/0.b.None", "1/1/1/1.d.None", "1/1/1/2.f.None", "1/1/2/", "1/1/2/0.h.None", "1/1/2/1.j.None", "1/1/2/2.l.None", "1/2/", "1/2/0/", "1/2/0/0.n.None", "1/2/0/1.p.None", "1/2/0/2.r.None"],
            ["0/", "0/2/", "0/2/1/", "0/2/1/0.v.None", "0/2/1/2.x.None", "0/2/2/", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/1/1/", "1/1/1/0.b.None", "1/1/1/1.d.None", "1/1/1/2.f.None", "1/1/2/", "1/1/2/0.h.None", "1/1/2/1.j.None", "1/1/2/2.l.None", "1/2/", "1/2/0/", "1/2/0/0.n.None", "1/2/0/1.p.None", "1/2/0/2.r.None", "1/2/1/", "1/2/1/0.t.None"],
            ["0/", "0/2/", "0/2/1/", "0/2/1/2.x.None", "0/2/2/", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/1/1/", "1/1/1/0.b.None", "1/1/1/1.d.None", "1/1/1/2.f.None", "1/1/2/", "1/1/2/0.h.None", "1/1/2/1.j.None", "1/1/2/2.l.None", "1/2/", "1/2/0/", "1/2/0/0.n.None", "1/2/0/1.p.None", "1/2/0/2.r.None", "1/2/1/", "1/2/1/0.t.None", "1/2/1/1.v.None"],
            ["0/", "0/2/", "0/2/2/", "0/2/2/1.z.None", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/1/1/", "1/1/1/0.b.None", "1/1/1/1.d.None", "1/1/1/2.f.None", "1/1/2/", "1/1/2/0.h.None", "1/1/2/1.j.None", "1/1/2/2.l.None", "1/2/", "1/2/0/", "1/2/0/0.n.None", "1/2/0/1.p.None", "1/2/0/2.r.None", "1/2/1/", "1/2/1/0.t.None", "1/2/1/1.v.None", "1/2/1/2.x.None"],
            ["0/", "0/2/", "0/2/2/", "0/2/2/2.a.None", "1/", "1/0/", "1/0/0/", "1/0/0/0.c.None", "1/0/0/1.e.None", "1/0/0/2.g.None", "1/0/1/", "1/0/1/0.i.None", "1/0/1/1.k.None", "1/0/1/2.m.None", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/1/1/", "1/1/1/0.b.None", "1/1/1/1.d.None", "1/1/1/2.f.None", "1/1/2/", "1/1/2/0.h.None", "1/1/2/1.j.None", "1/1/2/2.l.None", "1/2/", "1/2/0/", "1/2/0/0.n.None", "1/2/0/1.p.None", "1/2/0/2.r.None", "1/2/1/", "1/2/1/0.t.None", "1/2/1/1.v.None", "1/2/1/2.x.None", "1/2/2/", "1/2/2/0.z.None"],
        ]

        working = tempfile.mkdtemp()
        directory = tempfile.mkdtemp()

        try:
            c = DiskCache.overwrite(directory, 1024, maxperdir=3)

            for i in range(26):
                filename = os.path.join(working, "file{:02d}".format(i))
                open(filename, "w").write("hi")

                c.newfile(chr(i + ord("a")), None, filename)

                self.assertEqual(filling[i], list(lstree(directory)))

            c2 = DiskCache.adopt(directory, 1024, maxperdir=3)
            self.assertEqual(c.lookup, c2.lookup)
            self.assertEqual(c.numbytes, c2.numbytes)
            self.assertEqual(c.depth, c2.depth)
            self.assertEqual(c.number, c2.number)

            for i, n in enumerate(chr(j + ord("a")) for j in list(range(0, 26, 2)) + list(range(1, 26, 2))):
                c.touch(n)
                self.assertEqual(touching[i], list(lstree(directory)))

            c3 = DiskCache.adopt(directory, 1024, maxperdir=3)
            self.assertEqual(c.lookup, c3.lookup)
            self.assertEqual(c.numbytes, c3.numbytes)
            self.assertEqual(c.depth, c3.depth)
            self.assertEqual(c.number, c3.number)

            copy = os.path.join(working, "copy")
            shutil.copytree(directory, copy)

            c4 = DiskCache.adopt(copy, 1024, maxperdir=3)
            self.assertEqual(c.lookup, c4.lookup)
            self.assertEqual(c.numbytes, c4.numbytes)
            self.assertEqual(c.depth, c4.depth)
            self.assertEqual(c.number, c4.number)
            
            # do them in bulk (to avoid unnecessary directory listings)
            c.touch(*[chr(j + ord("a")) for j in range(0, 13)])

            # or do them one at a time
            for n in [chr(j + ord("a")) for j in range(0, 13)]:
                c4.touch(n)

            # should yield the same directory structure
            self.assertEqual(list(lstree(directory)), list(lstree(copy)))

            self.assertEqual(c.lookup, c4.lookup)
            self.assertEqual(c.numbytes, c4.numbytes)
            self.assertEqual(c.depth, c4.depth)
            self.assertEqual(c.number, c4.number)

            self.assertEqual(c.numbytes, 52)

            filename = os.path.join(working, "big")
            open(filename, "w").write("x" * (c.limitbytes - c.numbytes))
            c.newfile("big", None, filename)

            self.assertEqual(c.numbytes, 1024)
            self.assertEqual(list(lstree(directory)), ["1/", "1/0/", "1/0/2/", "1/0/2/0.o.None", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/2/", "1/2/0/", "1/2/0/0.n.None", "1/2/0/1.p.None", "1/2/0/2.r.None", "1/2/1/", "1/2/1/0.t.None", "1/2/1/1.v.None", "1/2/1/2.x.None", "1/2/2/", "1/2/2/0.z.None", "1/2/2/1.a.None", "1/2/2/2.b.None", "2/", "2/0/", "2/0/0/", "2/0/0/0.c.None", "2/0/0/1.d.None", "2/0/0/2.e.None", "2/0/1/", "2/0/1/0.f.None", "2/0/1/1.g.None", "2/0/1/2.h.None", "2/0/2/", "2/0/2/0.i.None", "2/0/2/1.j.None", "2/0/2/2.k.None", "2/1/", "2/1/0/", "2/1/0/0.l.None", "2/1/0/1.m.None", "2/1/0/2.big.None"])

            filename = os.path.join(working, "small1")
            open(filename, "w").write("x")
            c.newfile("small1", None, filename)

            self.assertEqual(c.numbytes, 1023)
            self.assertEqual(list(lstree(directory)), ["1/", "1/0/", "1/0/2/", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/2/", "1/2/0/", "1/2/0/0.n.None", "1/2/0/1.p.None", "1/2/0/2.r.None", "1/2/1/", "1/2/1/0.t.None", "1/2/1/1.v.None", "1/2/1/2.x.None", "1/2/2/", "1/2/2/0.z.None", "1/2/2/1.a.None", "1/2/2/2.b.None", "2/", "2/0/", "2/0/0/", "2/0/0/0.c.None", "2/0/0/1.d.None", "2/0/0/2.e.None", "2/0/1/", "2/0/1/0.f.None", "2/0/1/1.g.None", "2/0/1/2.h.None", "2/0/2/", "2/0/2/0.i.None", "2/0/2/1.j.None", "2/0/2/2.k.None", "2/1/", "2/1/0/", "2/1/0/0.l.None", "2/1/0/1.m.None", "2/1/0/2.big.None", "2/1/1/", "2/1/1/0.small1.None"])

            filename = os.path.join(working, "small2")
            open(filename, "w").write("x")
            c.newfile("small2", None, filename)

            self.assertEqual(c.numbytes, 1024)
            self.assertEqual(list(lstree(directory)), ["1/", "1/0/", "1/0/2/", "1/0/2/1.q.None", "1/0/2/2.s.None", "1/1/", "1/1/0/", "1/1/0/0.u.None", "1/1/0/1.w.None", "1/1/0/2.y.None", "1/2/", "1/2/0/", "1/2/0/0.n.None", "1/2/0/1.p.None", "1/2/0/2.r.None", "1/2/1/", "1/2/1/0.t.None", "1/2/1/1.v.None", "1/2/1/2.x.None", "1/2/2/", "1/2/2/0.z.None", "1/2/2/1.a.None", "1/2/2/2.b.None", "2/", "2/0/", "2/0/0/", "2/0/0/0.c.None", "2/0/0/1.d.None", "2/0/0/2.e.None", "2/0/1/", "2/0/1/0.f.None", "2/0/1/1.g.None", "2/0/1/2.h.None", "2/0/2/", "2/0/2/0.i.None", "2/0/2/1.j.None", "2/0/2/2.k.None", "2/1/", "2/1/0/", "2/1/0/0.l.None", "2/1/0/1.m.None", "2/1/0/2.big.None", "2/1/1/", "2/1/1/0.small1.None", "2/1/1/1.small2.None"])

            filename = os.path.join(working, "small3")
            open(filename, "w").write("hey, how's it goin?")
            c.newfile("small3", None, filename)

            self.assertEqual(c.numbytes, 1023)
            self.assertEqual(list(lstree(directory)), ["1/", "1/2/", "1/2/1/", "1/2/1/2.x.None", "1/2/2/", "1/2/2/0.z.None", "1/2/2/1.a.None", "1/2/2/2.b.None", "2/", "2/0/", "2/0/0/", "2/0/0/0.c.None", "2/0/0/1.d.None", "2/0/0/2.e.None", "2/0/1/", "2/0/1/0.f.None", "2/0/1/1.g.None", "2/0/1/2.h.None", "2/0/2/", "2/0/2/0.i.None", "2/0/2/1.j.None", "2/0/2/2.k.None", "2/1/", "2/1/0/", "2/1/0/0.l.None", "2/1/0/1.m.None", "2/1/0/2.big.None", "2/1/1/", "2/1/1/0.small1.None", "2/1/1/1.small2.None", "2/1/1/2.small3.None"])

            filename = os.path.join(working, "biggie")
            c.linkfile("big", filename)

            self.assertEqual(c.get("big"), "2/1/0/2.big.None")
            self.assertEqual(os.stat(c.getfile("big")).st_ino, os.stat(filename).st_ino)

            c.touch("big")
            self.assertEqual(c.get("big"), "2/1/2/0.big.None")
            self.assertEqual(os.stat(c.getfile("big")).st_ino, os.stat(filename).st_ino)

        finally:
            shutil.rmtree(working)
            shutil.rmtree(directory)
