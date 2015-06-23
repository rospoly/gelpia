use std::ops::{Add, Sub, Mul, Div, Neg};
use std::cmp::{PartialOrd, Ordering, PartialEq, Ord};
use std::f64::{NEG_INFINITY, INFINITY};

#[derive(Debug, Copy, Clone)]
pub struct Interval {
    pub inf: f64,
    pub sup: f64,
}

impl Interval {
    pub fn new(inf: f64,
               sup: f64) -> Interval{
        if inf > sup {
            panic!("Improper interval");
        }
        Interval{inf: inf, sup: sup}
    }
}

pub struct Quple {
    pub p: f64,
    pub pf: u32,
    pub data: Vec<Interval>,
}

impl PartialEq for Quple {
    fn eq(&self, other: &Quple) -> bool {
        self.pf == other.pf
    }
}

impl Eq for Quple { }

impl PartialOrd for Quple {
    fn partial_cmp(&self, other: &Quple) -> Option<Ordering> {
        if self.p > other.p {
            Some(Ordering::Greater)
        }
        else if self.pf > other.pf {
            Some(Ordering::Greater)
        }
        else {
            Some(Ordering::Less)
        }
    }
}

impl Ord for Quple {
    fn cmp(&self, other: &Quple) -> Ordering {
        if self.p > other.p {
            Ordering::Greater
        }
        else if self.pf > other.pf {
            Ordering::Greater
        }
        else if self.pf == other.pf {
            Ordering::Equal
        }
        else {
            Ordering::Less
        }
    }
}

impl Add for Interval {
    type Output = Interval;
    
    fn add(self, other: Interval) -> Interval {
        Interval::new(self.inf + other.inf,
                      self.sup + other.sup)
    }
}

impl Sub for Interval {
    type Output = Interval;
    
    fn sub(self, other: Interval) -> Interval {
        Interval::new(self.inf - other.sup,
                      self.sup - other.inf)
    }
}

impl Mul for Interval {
    type Output = Interval;
    
    fn mul(self, other: Interval) -> Interval {
        let a = self.inf;
        let b = self.sup;
        let c = other.inf;
        let d = other.sup;
        let ac = a*c;
        let ad = a*d;
        let bc = b*c;
        let bd = b*d;
        Interval::new(min(&[ac, ad, bc, bd]),
                      max(&[ac, ad, bc, bd]))
    }
}

impl Div for Interval {
    type Output = Interval;
    
    fn div(self, other: Interval) -> Interval {
        let a = self.inf;
        let b = self.sup;
        let c = other.inf;
        let d = other.sup;
        let ac = a/c;
        let ad = a/d;
        let bc = b/c;
        let bd = b/d;
        Interval::new(min(&[ac, ad, bc, bd]),
                      max(&[ac, ad, bc, bd]))
    }
}

impl Neg for Interval {
    type Output = Interval;

    fn neg(self) -> Interval {
        Interval::new(-self.sup,
                      -self.inf)
    }
}

pub fn min(args: &[f64]) -> f64 {
    let mut min = INFINITY;
    for &arg in args {
        if arg < min {
            min = arg;
        }
    }
    min
}

pub fn abs(i: Interval) -> Interval {
    if i.inf >= 0.0 { // Interval is already positive
        i
    }
    else if i.sup <= 0.0 { // Interval is completely negative
        Interval::new(-i.sup, -i.inf)
    }
    else { // Otherwise interval spans 0.
        Interval::new(0.0, max(&[-i.inf, i.sup]))
    }
}

pub fn max(args: &[f64]) -> f64 {
    let mut max = NEG_INFINITY;
    for &arg in args {
        if arg > max {
            max = arg;
        }
    }
    max
}

pub fn pow_d(a: f64, b: u32) -> f64 {
    if b == 0 {
        1.0
    }
    else if b == 1 {
        a
    }
    else {
        let mut result;
        let half_pow = pow_d(a, b/2);
        if b%2 == 1 {
            result = half_pow * half_pow*a;
        }
        else {
            result = half_pow*half_pow;
        }
        result
    }
}

pub fn pow(a: Interval, b: u32) -> Interval {
    if b % 2 == 1 {
        Interval::new(pow_d(a.inf, b), pow_d(a.sup, b))
    }
    else {
        if a.inf >= 0.0 {
            Interval::new(pow_d(a.inf, b), pow_d(a.sup, b))                
        }
        else if a.sup < 0.0 {
            Interval::new(pow_d(a.sup, b), pow_d(a.inf, b))
        }
        else {
            Interval::new(0.0, max(&[pow_d(a.inf, b),
                                     pow_d(a.sup, b)]))
        }
    }
}

pub fn width(i: &Interval) -> f64 {
    let w = i.sup - i.inf;
    if w < 0.0 {
        -w
    }
    else {
        w
    }
}

pub fn width_box(x: &Vec<Interval>) -> f64 {
    let mut result = NEG_INFINITY;
    for i in x {
        let w = width(i);
        if w > result {
            result = w;
        }
    }
    result
}

pub fn split(x: &Vec<Interval>) -> Vec<Vec<Interval>> {
    let mut widest = NEG_INFINITY;
    let mut idx = -1;
    for i in (0..x.len()) {
        let w = width(&x[i]);
        if w > widest {
            widest = w;
            idx = i;
        }
    }
    
    let mid = (x[idx].inf +x[idx].sup)/2.0;
    
    let mut result = vec![x.clone(), x.clone()];
    result[0][idx].sup = mid;
    result[1][idx].inf = mid;
    result
}

pub fn midpoint(x: &Vec<Interval>) -> Vec<Interval> {
    let mut result = Vec::new();
    for i in x {
        let mid = (i.inf + i.sup)/2.0;
        result.push(Interval::new(mid,
                                  mid));
    }
    result
}
