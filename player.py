import copy
class Player:
    def __init__(self, name, rating, primary_pos, secondary_pos, set, ht, wt, ins, mid, three, plk, itd, prd, reb, ath, ppg, rpg, apg, mpg, spg, bpg, fgp, three_p, ftp):
        self.name = name
        self.rating = rating
        self.primary_pos = primary_pos
        self.secondary_pos = secondary_pos
        self.set = set
        self.desc = ""
        self.pic = ""
        self.ht = ht
        self.wt = str(wt) + "lbs"
        self.ins = ins
        self.mid = mid
        self.three = three
        self.plk = plk
        self.itd = itd
        self.prd = prd
        self.reb = reb
        self.ath = ath
        self.ppg = ppg
        self.rpg = rpg
        self.apg = apg
        self.mpg = mpg
        self.spg = spg
        self.bpg = bpg
        self.fgp = fgp
        self.three_p = three_p
        self.ftp = ftp
        self.compare = False

    def __str__(self):
        return self.name

    def clone(self):
            return copy.deepcopy(self)

    def convert_positions(self):
        if self.secondary_pos == "":
            positions = self.primary_pos
        else:
            positions = self.primary_pos+"/"+self.secondary_pos
        return positions

    def to_dict(self):
        return {"Name": self.name,
        "Rating": self.rating,
        "Positions": self.convert_positions(),
        "Height":      self.ht,
        "Weight":      self.wt,
        "Inside Scoring":     self.ins,
        "Mid Range Shooting":     self.mid,
        "3PT Shooting":    self.three,
        "Playmaking":     self.plk,
        "Interior Defense":     self.itd,
        "Perimeter Defense":     self.prd,
        "Rebounding":     self.reb,
        "Athleticism":     self.ath,
        "PPG":     self.ppg,
        "RPG":     self.rpg,
        "APG":     self.apg,
        "MPG":     self.mpg,
        "SPG":     self.spg,
        "BPG":     self.bpg,
        "FG%":     self.fgp,
        "3P%": self.three_p,
        "FT%":     self.ftp,
    }
