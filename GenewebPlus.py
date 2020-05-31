#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004  Martin Hawlisch
# Copyright (C) 2004-2006, 2008 Donald N. Allingham
# Copyright (C) 2008  Brian G. Matherly
# Copyright (C) 2009  Gary Burton
# Copyright (C) 2010       Jakim Friant
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"Export to GeneWeb."

#-------------------------------------------------------------------------
#
# Standard Python Modules
#
#-------------------------------------------------------------------------
import os

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
import collections
import re
log = logging.getLogger(".WriteGeneWeb")

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext
from gramps.gen.lib import Date, Event, EventType, FamilyRelType, PlaceType,Person , EventRoleType
from gramps.gui.plug.export import WriterOptionBox
from gramps.gen.utils.alive import probably_alive
from gramps.gui.glade import Glade
from gramps.gen.config import config
from gramps.gen.display.place import displayer as _pd
from gramps.gen.display import place
from gramps.gen.lib.date import Today
from gramps.gen.utils.location import get_location_list

FAMILYCONSTANTEVENTS = {
    EventType.ANNULMENT  : "#anul",
    EventType.DIV_FILING : "#div",
    EventType.DIVORCE    : "#div",
    EventType.CENSUS     : "#census",
    EventType.ENGAGEMENT : "#enga",
    EventType.MARR_BANNS : "#marb",
    EventType.MARR_CONTR : "#marc",
    EventType.MARR_LIC   : "#marl",
    EventType.MARR_SETTL : "#marc",
    EventType.MARRIAGE   : "#marr"
    }

PERSONCONSTANTEVENTS = {
    EventType.ADOPT            : "#adoption",
    EventType.ADULT_CHRISTEN   : "#bapt",
    EventType.BIRTH            : "#birt",
    EventType.DEATH            : "#deat",
    EventType.BAPTISM          : "#bapt",
    EventType.BAR_MITZVAH      : "#barm",
    EventType.BAS_MITZVAH      : "#basm",
    EventType.BLESS            : "#bles",
    EventType.BURIAL           : "#buri",
    EventType.CAUSE_DEATH      : "#cause_de_la_mort",
    EventType.ORDINATION       : "#ordn",
    EventType.CENSUS           : "#cens",
    EventType.CHRISTEN         : "#bapt" ,
    EventType.CONFIRMATION     : "#conf",
    EventType.CREMATION        : "#crem",
    EventType.DEGREE           : "#degr",
    EventType.DIV_FILING       : "#divers",
    EventType.EDUCATION        : "#education",
    EventType.ELECTED          : "#elec",
    EventType.EMIGRATION       : "#emig",
    EventType.FIRST_COMMUN     : "#first_common",
    EventType.GRADUATION       : "#grad",
    EventType.MED_INFO         : "#info_medicale",
    EventType.MILITARY_SERV    : "#mser",
    EventType.NATURALIZATION   : "#natu",
    EventType.NOB_TITLE        : "#title",
    EventType.NUM_MARRIAGES    : "#nmr",
    EventType.IMMIGRATION      : "#immi",
    EventType.OCCUPATION       : "#occu",
    EventType.PROBATE          : "#probation",
    EventType.PROPERTY         : "#prop",
    EventType.RELIGION         : "#religion",
    EventType.RESIDENCE        : "#resi",
    EventType.RETIREMENT       : "#reti",
    EventType.WILL             : "#will",
    }

RELATIONCONSTANTEVENTS = {
    "Père Adoptif"            : "adop fath" ,
    "Mère Adoptive"           : "adop moth" ,
    "Père Reconnu"            : "reco fath" ,
    "Mère Reconnue"           : "reco moth" ,
    "Père Possible"           : "cand fath" ,
    "Mère Possible"           : "cand moth" ,
    "Père Nourricier"         : "fost fath" ,
    "Mère Nourricière"        : "fost moth" ,
    "Parrain"                 : "godp fath" ,
    "Marraine"                : "godp moth" ,
    }

RELATIONEVENTS = {
    "Parrain"                 : "godp fath" ,
    "Marraine"                : "godp moth" ,
    }

WITNESSROLETYPE = [
    EventRoleType.WITNESS,
    EventRoleType.CELEBRANT,
    EventRoleType.INFORMANT,
    EventRoleType.CLERGY,
    EventRoleType.AIDE,
    EventRoleType.CUSTOM,
    EventRoleType.BRIDE,
    EventRoleType.GROOM,
    EventRoleType.FAMILY,
    ]

class PlaceDisplayGeneanet(place.PlaceDisplay):

    def __init__(self):
        super(PlaceDisplayGeneanet,self).__init__()

    def display(self, db, place, date=None, fmt=-1):
        if not place:
            return ""
        if not config.get('preferences.place-auto'):
            return place.title
        else:
            if fmt == -1:
                fmt = config.get('preferences.place-format')
            pf = self.place_formats[fmt]
            lang = pf.language
            places = get_location_list(db, place, date, lang)
            visited = [place.handle]
            postal_code = place.get_code()
            if not postal_code:
                place2 =""
                for placeref in place.placeref_list:
                    place2 = db.get_place_from_handle(placeref.ref)
                    if place2:
                        postal_code = self._find_postal_code(db,place2,visited)
                        if postal_code:
                            break
            return  self._find_populated_place(places,place,postal_code)

    def _find_postal_code(self,db,place,visited):
        postal_code = place.get_code()
        if postal_code:
            return postal_code
        else:
            for placeref in place.placeref_list:
                if placeref.ref not in visited:
                    place2 = db.get_place_from_handle(placeref.ref)
                    if place2:
                        visited.append(place2.handle)
                        postal_code = self._find_postal_code(db,place2,visited)
                        if postal_code:
                            break
            return postal_code

    def _find_populated_place(self,places,place,postal_code):
        populated_place = ""
        level = 0
        for index, item in enumerate(places):
            if int(item[1]) in [PlaceType.NUMBER, PlaceType.BUILDING , PlaceType.FARM , PlaceType.HAMLET, PlaceType.NEIGHBORHOOD , PlaceType.STREET , PlaceType.PARISH , PlaceType.LOCALITY , PlaceType.BOROUGH, PlaceType.UNKNOWN]:
                level = 1
                if populated_place == "":
                    populated_place = "[ " + item[0]
                else :
                    populated_place = populated_place + " - " + item[0]
            elif int(item[1]) in [PlaceType.CITY, PlaceType.VILLAGE,
                            PlaceType.TOWN]:
                level = 2
                if populated_place == "":
                    populated_place = item[0]
                else:
                    populated_place = populated_place + " ] - " + item[0]
                populated_place = populated_place + ", "  + postal_code
            elif int(item[1]) in [PlaceType.COUNTY, PlaceType.DEPARTMENT ]:
                if populated_place == "":
                    populated_place = item[0]
                else:
                    if level == 1:
                        populated_place = populated_place + " ] - ,, " + item[0]
                    else:
                        populated_place = populated_place + ", " + item[0]
                    level = 3
            elif int(item[1]) in [PlaceType.STATE, PlaceType.REGION , PlaceType.PROVINCE ]:
                if populated_place == "":
                    populated_place = item[0]
                else:
                    if level == 1:
                        populated_place = populated_place + " ] - ,,, " + item[0]
                    elif level ==  2:
                        populated_place = populated_place + ",, " + item[0]
                    else:
                         populated_place = populated_place + ", " + item[0]
                    level = 4
            elif int(item[1]) in [PlaceType.COUNTRY ]:
                if populated_place == "":
                    populated_place = item[0]
                else:
                    if level == 1:
                        populated_place = populated_place + " ] - ,,,, " + item[0]
                    elif level ==  2:
                        populated_place = populated_place + ",,, " + item[0]
                    elif level == 3:
                        populated_place = populated_place + ",, " + item[0]
                    else:
                        populated_place = populated_place + ", " + item[0]
                    level = 5
        return populated_place

class GeneWebPlusWriter(object):
    def __init__(self, database, filename, user, option_box=None):
        self.db = database
        self.filename = filename
        self.user = user
        self.option_box = option_box
        if isinstance(self.user.callback, collections.Callable): # callback is really callable
            self.update = self.update_real
        else:
            self.update = self.update_empty

        self.persons_details_done = []
        self.persons_notes_done = []
        self.person_ids = {}
        self.second = []
        self.child = []
        
        if option_box:
            self.option_box.parse_options()
            self.db = option_box.get_filtered_database(self.db)

    def update_empty(self):
        pass

    def update_real(self):
        self.count += 1
        newval = int(100*self.count/self.total)
        if newval != self.oldval:
            self.user.callback(newval)
            self.oldval = newval

    def writeln(self, text):
        self.g.write('%s\n' % (text))

    def export_data(self):

        self.dirname = os.path.dirname (self.filename)
        try:
            self.g = open(self.filename, "w")
        except IOError as msg:
            msg2 = _("Could not create %s") % self.filename
            self.user.notify_error(msg2, str(msg))
            return False
        except:
            self.user.notify_error(_("Could not create %s") % self.filename)
            return False

        self.flist = [x for x in self.db.iter_family_handles()]
        if len(self.flist) < 1:
            self.user.notify_error(_("No families matched by selected filter"))
            return False
        
        self.count = 0
        self.oldval = 0
        self.total = len(self.flist)
        self.writeln("encoding: utf-8")
        self.writeln("gwplus")
        for key in self.flist:
            self.write_family(key)
            self.writeln("")
        
        self.plist = [x for x in self.db.iter_person_handles()]
        if len(self.plist) < 1:
            self.user.notify_error(_("No person matched by selected filter"))
            return False
        
        self.count = 0
        self.oldval = 0
        self.total = len(self.plist)
        for key in self.plist:
            self.write_person(key,0)
            self.write_rel(key)
        self.writeln("")
        
        for key in self.second:
            self.write_person(key,1)
        self.writeln("")

        for key in self.plist:
            self.write_note_of_person(key)
            self.writeln("")

        self.g.close()
        return True
    
    def write_rel(self, person_handle):
# ecrir les relations d'une personne
# on parcourt les relations ainsi que les 
# evenemenet baptemes pour les parrains et marraines
        person = self.db.get_person_from_handle(person_handle)
        output=""
        if person:
# dans les relation le nom est reduit
            pname = self.get_ref_name_redux(person)
            for ref in person.get_person_ref_list():
                pers = self.db.get_person_from_handle(ref.ref)
                if pers:
                    name = self.get_name(pers)
                    relation = ref.get_relation()
                    if relation in RELATIONCONSTANTEVENTS:
                        output += "\n- %s: %s" % (RELATIONCONSTANTEVENTS[relation] , name)
                   #     self.writeln("- %s: %s" % (RELATIONCONSTANTEVENTS[relation] , name))
          #          else:
          #              self.writeln("- %s: %s" % (relation , name))
            for event_ref in person.get_event_ref_list(): 
                role = int(event_ref.get_role())
                if role != EventRoleType.PRIMARY:
                    next
                else:
                    event = self.db.get_event_from_handle(event_ref.ref)
                    etype = int(event.get_type())
                    if etype in (EventType.BAPTISM, EventType.CHRISTEN):
                        for (objclass, handle) in self.db.find_backlink_handles(event.handle, ['Person']):
                            person2 = self.db.get_person_from_handle(handle)
                            if person2 and person2 != person:
                                for ref in person2.get_event_ref_list():
                                    if (ref.ref == event.handle):
                                        if (int(ref.get_role()) == EventRoleType.CUSTOM):
                                            relation = str(ref.get_role())
                                            name = self.get_name(person2)
                                         #   self.writeln("- %s: %s" % ( relation , name))
                                            if relation in RELATIONEVENTS:
                                                #self.writeln("- %s: %s" % (RELATIONEVENTS[relation] , name))
                                                output += "\n- %s: %s" % (RELATIONEVENTS[relation] , name)
            if output:
                self.writeln("rel %s" % pname)
                self.writeln("beg %s" % output)
                self.writeln("end") 
        return

    def write_person(self, person_handle , sec):
# on ecrit les personnes
# on shifte les personnes qui n'ont pas ete ecrite en full
# on les mets dans le tableau second pour le second passage
# au second passage si ils n'ont pas ecrit en full il faut leur
# rajouter une famille        
        person = self.db.get_person_from_handle(person_handle)
        if person:
            if self.persons_details_done.count(person_handle) == 0 and sec == 0:
                self.second.append(person_handle)
            elif self.persons_details_done.count(person_handle) == 0 and sec == 1:
                self.addfam(person_handle)
                name = self.get_ref_name_redux(person)
                self.write_pevent(person,name)
            else:
                self.update()
                name = self.get_ref_name_redux(person)
                self.write_pevent(person,name)

    def addfam(self, person_handle):
        self.writeln ("fam ? ? + ? ? ")
        self.writeln("beg")
        child = self.db.get_person_from_handle(person_handle)
        gender = ""
        if child.get_gender() == Person.MALE:
            gender = "h"
        elif child.get_gender() == Person.FEMALE:
            gender = "f"
        father_lastname = ""
        (refname , othername ) = self.get_child_ref_name(child, father_lastname)
        self.writeln("- %s %s %s %s" %
                            (gender,
                            refname,
                            othername,
                            self.get_full_person_info_child(child)
                            )
                         )
        self.writeln("end")

    def is_child(self,person_handle):
        is_child = 0
        if person_handle:
            person = self.db.get_person_from_handle(person_handle)
            if person:
                pf_list = person.get_parent_family_handle_list()
                if pf_list:
                    for family_handle in pf_list:
                        if family_handle in self.flist:
                            is_child = 1
        return is_child

    def write_family(self, family_handle):
        father_done=0
        mother_done=0
        family = self.db.get_family_from_handle(family_handle)
        if family:
            self.update()
            father_handle = family.get_father_handle()
            mother_handle = family.get_mother_handle()
            if father_handle in self.persons_details_done or self.is_child(father_handle):
                father_done=1
            if mother_handle in self.persons_details_done or self.is_child(mother_handle):
                mother_done=1
            if father_handle:
                father = self.db.get_person_from_handle(father_handle)
                if mother_handle:
                    mother = self.db.get_person_from_handle(mother_handle)
                    ( mname , mothername ) = self.get_ref_name(father)
                    ( fname , fothername ) = self.get_ref_name(mother)
                    if father_done: 
                        if mother_done:
                            self.writeln("fam %s +%s %s" % (mname , self.get_wedding_data(family), fname ))
                        elif fothername:
                            self.writeln("fam %s +%s %s %s %s" % (mname , self.get_wedding_data(family) , fname , fothername, self.get_full_person_info_fam(mother)))
                        else:
                            self.writeln("fam %s +%s %s %s" % (mname , self.get_wedding_data(family) , fname , self.get_full_person_info_fam(mother)))
                    elif mother_done:
                        self.writeln("fam %s %s %s+%s %s " %
                            (mname,mothername, self.get_full_person_info_fam(father), 
                            self.get_wedding_data(family), 
                            fname 
                            )
                         )
                    elif fothername:
                        self.writeln("fam %s %s %s+%s %s %s %s" %
                            (mname,mothername, 
                            self.get_full_person_info_fam(father), 
                            self.get_wedding_data(family), 
                            fname , fothername,
                            self.get_full_person_info_fam(mother)
                            )
                         )
                    else:
                        self.writeln("fam %s %s %s+%s %s %s" %
                            (mname,mothername, 
                            self.get_full_person_info_fam(father), 
                            self.get_wedding_data(family), 
                            fname , 
                            self.get_full_person_info_fam(mother)
                            )
                         )
                else:
                    mother = None
                    ( mname , mothername ) = self.get_ref_name(father)
                    if father_done: 
                        self.writeln("fam %s +%s %s %s" %
                            ( mname ,
                            self.get_wedding_data(family), 
                            "? ?",
                            ""
                            )
                         )
                    else:
                        self.writeln("fam %s %s %s+%s %s %s" %
                            ( mname , mothername, self.get_full_person_info_fam(father),
                            self.get_wedding_data(family), 
                            "? ?",
                            ""
                            )
                         )
                 
            else:
                mother_handle = family.get_mother_handle()
                father = None
                if mother_handle:
                    mother = self.db.get_person_from_handle(mother_handle)
                    ( fname , fothername ) = self.get_ref_name(mother)
                    if mother_done:
                        self.writeln("fam %s %s+%s %s" %
                            ("? ?", 
                            "", 
                            self.get_wedding_data(family), 
                            fname , 
                                )
                             )
                    elif fothername:
                        self.writeln("fam %s %s+%s %s %s %s" %
                            ("? ?", 
                            "", 
                            self.get_wedding_data(family), 
                            fname , fothername,
                            self.get_full_person_info_fam(mother)
                                )
                             )
                    else:
                        self.writeln("fam %s %s+%s %s %s" %
                            ("? ?", 
                            "", 
                            self.get_wedding_data(family), 
                            fname ,
                            self.get_full_person_info_fam(mother)
                                )
                             )
                else:
                    mother = None
                    self.writeln("fam ? ? +? ? ? ")
            self.write_witness( family)
            self.write_sources( family.get_citation_list())
            if True: # FIXME: not (self.restrict and self.exclnotes):
                notelist = family.get_note_list()
                note = ""
                for notehandle in notelist:
                    noteobj = self.db.get_note_from_handle(notehandle)
                    note += noteobj.get() + "<BR>"
                    if note and note != "":
                        note = note.replace('\n\r',' ')
                        note = note.replace('\r\n',' ')
                        note = note.replace('\n',' ')
                        note = note.replace('\r',' ')
                if note:
                    self.writeln("comm %s" % note)
                    
            self.write_fevent( family)

            self.write_children( family, father)
#            self.write_notes( family, father, mother)

    def write_fevent(self, family):
        deb = 1
        for event_ref in family.get_event_ref_list():
            event = self.db.get_event_from_handle(event_ref.ref)
            if event and deb == 1:
                deb = 0
                self.writeln("fevt")
            self._process_family_event(event, event_ref)
        if deb == 0:
            self.writeln("end fevt")    

    def write_pevent(self, person,name):
        output=0
        first=1
        for event_ref in person.get_event_ref_list():
            role = int(event_ref.get_role())
            if role != EventRoleType.PRIMARY:
                next
            else:
                output=1
                if first:
                    self.writeln("pevt %s" % name)
                    first=0
                event = self.db.get_event_from_handle(event_ref.ref)
                self._process_person_event(event, event_ref)
        if output:
            self.writeln("end pevt")    

    def _process_family_event(self, event, event_ref):
        etype = int(event.get_type())
        val = FAMILYCONSTANTEVENTS.get(etype)
        if val is None:
           the_type = str(event.get_type())
           if the_type:
               val = "#" + the_type
           else:
               val =" #None"
        descr = event.get_description()
        res = self._get_event_data(event)
        val = val + " " + res
        self.writeln("%s" % val)
        self._witness_event(event,event_ref)
        return

    def _process_person_event(self, event, event_ref):
        output=""
        etype = int(event.get_type())
        val = PERSONCONSTANTEVENTS.get(etype)
        if val is None:
           the_type = str(event.get_type())
           if the_type:
               val = "#" + self.rem_spaces(the_type)
           else:
               val =" #None"
        descr = event.get_description()
        res = self._get_event_data(event)
        val = val + " " + res
        self.writeln("%s" % val)
        self._witness_event(event,event_ref)
        if descr:
            self.writeln("note %s" % descr)
        return

    def _witness_event(self,event,event_ref):
        for (objclass, handle) in self.db.find_backlink_handles(event.handle, ['Person']):
            person = self.db.get_person_from_handle(handle)
            self._write_witness_person(person,event)

    def _write_witness_person(self,person,event):
            if person:
                for ref in person.get_event_ref_list():
                    if (ref.ref == event.handle and int(ref.get_role()) in WITNESSROLETYPE):
                        gender = ""
                        if person.get_gender() == Person.MALE:
                            gender = "m"
                        elif person.get_gender() == Person.FEMALE:
                            gender = "f"
                        ( name , othername ) = self.get_ref_name(person)
                        person_handle = person.get_handle()
                        if person_handle in self.persons_details_done or self.is_child(person_handle):
                            self.writeln("wit %s: %s" %
                                    (gender,
                                    name,
                                    )
                                )
                        else:
                            self.writeln("wit %s: %s %s %s" %
                                    (gender,
                                    name , othername ,
                                    self.get_full_person_info_child(person)
                                    )
                                )

    def _get_event_data(self,event):
        ret = "";
        place_name = "";
        source_txt = "";
        date = self.format_date( event.get_date_object())
        place_handle = event.get_place_handle()
        if place_handle:
            displayer=PlaceDisplayGeneanet()
            dateobj2=Today()
            place = self.db.get_place_from_handle(place_handle)
            place_name = displayer.display(self.db, place, dateobj2)
            log.debug(" place_name %s" % place)
        source = self.get_primary_source( event.get_citation_list())
        if source:
            source_txt=self.get_source_txt(source)
        if date != "":
            ret = ret + date
        if place_name != "" and source_txt != "":
            ret = ret + " #p %s #s %s" % (self.rem_spaces( place_name), self.rem_spaces(source_txt))
        if place_name != "" and source_txt == "":
            ret = ret + " #p %s" % self.rem_spaces( place_name)
        if source_txt != "" and place_name  == "":
            ret = ret + " #s %s" % self.rem_spaces( source_txt)
        return ret

    def get_source_txt(self , source):
        source_txt =""
        title = source.get_title()
        if title:
            source_txt = title
        author = source.get_author()
        if author:
            source_txt = source_txt + "-" + author
        publication = source.get_publication_info()
        if publication:
           source_txt = source_txt + "-_" + publication  
        for reporef in source.get_reporef_list():
            repo = self.db.get_repository_from_handle(reporef.ref)
            if repo is None:
                next
            name = repo.get_name()
            if name:
                source_txt = source_txt + "_-" + name
        return source_txt    
      
    def write_witness(self, family):
        # FIXME: witnesses are not in events anymore
    
        event_ref_list = family.get_event_ref_list()
        for event_ref in event_ref_list:
            event = self.db.get_event_from_handle(event_ref.ref)
#            self.writeln("desc %s" % event.get_description())
            if event.type == EventType.MARRIAGE:
                for (objclass, handle) in self.db.find_backlink_handles(event.handle, ['Person']):
                    person = self.db.get_person_from_handle(handle)
                    if person:
                        self._write_witness_person(person,event)

    def write_sources(self,reflist):
        # FIXME
        #if self.restrict and self.exclnotes:
        #    return
            
        sourcetxt =""
        if reflist:
            for handle in reflist:
                citation = self.db.get_citation_from_handle(handle)
                src_handle = citation.get_reference_handle()
                source = self.db.get_source_from_handle(src_handle)
                if source:
                    if sourcetxt:
                        sourcetxt += "__" + self.rem_spaces(self.get_source_txt(source))
                    else:
                        sourcetxt = self.rem_spaces(self.get_source_txt(source))
        if sourcetxt:
            self.writeln( "src %s" % sourcetxt)

    def write_children(self,family, father):
        father_lastname = ""
        if father != None:
            father_lastname = father.get_primary_name().get_surname()
        child_ref_list = family.get_child_ref_list()
        if child_ref_list:
            self.writeln("beg")
            for child_ref in child_ref_list:
                child = self.db.get_person_from_handle(child_ref.ref)
                if child:
                    gender = ""
                    if child.get_gender() == Person.MALE:
                        gender = "h"
                    elif child.get_gender() == Person.FEMALE:
                        gender = "f"
                    child_done = 0
                    if child_ref.ref in self.persons_details_done:
                        child_done=1
                    (refname , othername ) = self.get_child_ref_name(child, father_lastname)
                    if child_done:
                        self.writeln("- %s %s " % 
                            (gender, 
                            refname, 
                            )
                         )
                    else:
                        self.writeln("- %s %s %s %s" % 
                            (gender, 
                            refname, 
                            othername,
                            self.get_full_person_info_child(child)
                            )
                         )
            self.writeln("end")

    def write_notes(self,family, father, mother):
        # FIXME:
        #if self.restrict and self.exclnotes:
        #    return
            
        if father != None:
            self.write_note_of_person(father)
        if mother != None:
            self.write_note_of_person(mother)
        child_ref_list = family.get_child_ref_list()
        if child_ref_list:
            for child_ref in child_ref_list:
                child = self.db.get_person_from_handle(child_ref.ref)
                if child:
                    self.write_note_of_person(child)

    def get_name(self,person): 
# get_name donne le nom d'une personne
# reduit si la personne a deja ete traité
# full si la personne n'a pas ete traité.
        if self.persons_details_done.count(person.get_handle()) == 0:
            self.persons_details_done.append(person.get_handle())
            ( nam , othernam ) = self.get_ref_name(person)
            info = self.get_full_person_info(person)
            if othernam:
                name = nam + " " + othernam + " " + info
            else:
                name = nam + " " + info
        else:
            name = self.get_ref_name_redux(person)
        return name

    def write_note_of_person(self,handle):
        person = self.db.get_person_from_handle(handle)
        if person:
            if self.persons_notes_done.count(person.get_handle()) == 0:
                self.persons_notes_done.append(person.get_handle())
            
                notelist = person.get_note_list()
                note = ""
                for notehandle in notelist:
                    noteobj = self.db.get_note_from_handle(notehandle)
                    note += noteobj.get()
                    note += "\n"

                for ref in person.get_person_ref_list():
                    relation = ref.get_relation()
                    if relation not in RELATIONCONSTANTEVENTS:
                        pers = self.db.get_person_from_handle(ref.ref)
                        if pers:
                            name = self.get_ref_name_redux(pers)
                            note += "Relie avec: " + name + " " + relation + "\n"
                            note += " "
                    
                if note and note != "":
                    name = self.get_name(person)
                    self.writeln("")
                    self.writeln("notes %s" % name)
                    self.writeln("beg")
                    self.writeln(note)
                    self.writeln("end notes")
    
    def get_full_person_info(self, person):
            
            retval = ""
            b_date = "0"
            b_place = ""
            birth_ref = person.get_birth_ref()
            for event_ref in person.get_event_ref_list():
                role = int(event_ref.get_role())
                if role != EventRoleType.PRIMARY:
                    next
                event = self.db.get_event_from_handle(event_ref.ref)
                etype = int(event.get_type())
                val = PERSONCONSTANTEVENTS.get(etype)

            if birth_ref:
                birth = self.db.get_event_from_handle(birth_ref.ref)
                if birth:
                    b_date = self.format_date( birth.get_date_object())
                    if not b_date:
                        b_date="0"
                    place_handle = birth.get_place_handle()
                    if place_handle:
                        b_place = _pd.display_event(self.db, birth)
        
            if probably_alive(person,self.db):
                d_date = ""
            else:
                d_date = "0"
            d_place = ""
            death_ref = person.get_death_ref()
            if death_ref:
                death = self.db.get_event_from_handle(death_ref.ref)
                if death:
                    d_date = self.format_date( death.get_date_object())
                    place_handle = death.get_place_handle()
                    if place_handle:
                        d_place = _pd.display_event(self.db, death)
            
            retval = retval + "%s " % b_date
            if b_place != "":
                retval = retval + "#bp %s " % self.rem_spaces(b_place)
            retval = retval + "%s " % d_date
            if d_place != "":
                retval = retval + "#dp %s " % self.rem_spaces(d_place)
            return retval

    def get_full_person_info_fam(self, person):
        """Output full person data of a family member.
        
        This is only done if the person is not listed as a child.
         
        """
        retval = ""
        if self.persons_details_done.count(person.get_handle()) == 0:
            is_child = 0
            pf_list = person.get_parent_family_handle_list()
            if pf_list:
                for family_handle in pf_list:
                    if family_handle in self.flist:
                        is_child = 1
            if is_child == 0:
                self.persons_details_done.append(person.get_handle())
                retval = self.get_full_person_info(person)
        return retval
                    
    def get_full_person_info_child(self, person):
        """Output full person data for a child, if not printed somewhere else."""
        retval = ""
        if self.persons_details_done.count(person.get_handle()) == 0:
            self.persons_details_done.append(person.get_handle())
            retval = self.get_full_person_info(person)
        return retval

    def rem_spaces(self,str):
        str = re.sub(r'^"','_"',str)
        str = re.sub(r'^\(','_(',str)
        return str.replace(' ','_')
    
    def get_ref_name_redux(self,person):
# donne le nom reduit d'une personne
        #missing_surname = config.get("preferences.no-surname-text")
        surn = person.get_primary_name().get_surname()
        if not surn:
            surname = "?"
        else:
            surname = self.rem_spaces(surn)
        #firstname = config.get('preferences.private-given-text') 
        #if not (probably_alive(person,self.db) and \
        #  self.restrict and self.living):
        name = person.get_primary_name()
        suffix = name.get_suffix()
        firstn = name.get_first_name()
        if not firstn:
            firstname = "?"
        else:
            firstname = self.rem_spaces(firstn)
        if suffix:
            firstname += "_" + self.rem_spaces(suffix)
        if person.get_handle() not in self.person_ids:
            self.person_ids[person.get_handle()] = len(self.person_ids)
        ret = "%s %s.%d" % (surname, firstname,
                             self.person_ids[person.get_handle()])
  #      self.writeln("DEB %s %s.%d" % (surname, firstname,len(self.person_ids)))
        return ret 

    def get_ref_name(self,person):
        #missing_surname = config.get("preferences.no-surname-text")
        name = person.get_primary_name()
        surname = self.rem_spaces( person.get_primary_name().get_surname())
        #firstname = config.get('preferences.private-given-text') 
        #if not (probably_alive(person,self.db) and \
        #  self.restrict and self.living):
        othername =""
        ret = self.get_ref_name_redux(person)
        nick = self.rem_spaces(name.get_nick_name())
        if nick:
           othername = "#nick %s" % nick
        for name in person.get_alternate_names():
            firstnam = self.rem_spaces(name.get_first_name().strip())
            suffix = ""
            surname = self.rem_spaces(name . get_surname())
            suffix = name.get_suffix()
            if firstnam:
                if suffix:
                    alias = "#alias %s_/%s_%s/" % ( firstnam, self.rem_spaces(suffix) , surname )
                else:
                    alias = "#alias %s_/%s/" % ( firstnam, surname )
            else:
                if suffix:
                    alias = "#alias %s_/%s/" % ( self.rem_spaces(suffix) , surname )
                else:
                    alias = "#alias /%s/" % ( surname )
           
            othername += " " + alias
        title= self.get_title(person)
        if title:
            othername += " " + title
        if self.persons_details_done.count(person.get_handle()) == 1:
            othername = ""
        return ret,othername

    def get_child_ref_name(self,person,father_lastname):
        #missing_first_name = config.get("preferences.no-given-text")
        othername =""
        name = person.get_primary_name()
        surn = name.get_surname()
        if not surn:
            surname = "?"
        else:
            surname = self.rem_spaces(surn)
        #firstname = config.get('preferences.private-given-text')
        #if not (probably_alive(person,self.db) and \
        #  self.restrict and self.living):
        firstn = name.get_first_name()
        if not firstn:
            firstname = "?"
        else:
            firstname = self.rem_spaces(firstn)
        if person.get_handle() not in self.person_ids:
            self.person_ids[person.get_handle()] = len(self.person_ids)
        suffix = name.get_suffix()
        if suffix:
            ret = "%s_%s.%d" % (firstname, self.rem_spaces(suffix) , self.person_ids[person.get_handle()])
        else:
            ret = "%s.%d" % (firstname, self.person_ids[person.get_handle()])
        if surname != father_lastname: ret += " " + surname
        nick = self.rem_spaces(name.get_nick_name())
        if nick:
           othername = "#nick %s" % nick
        for name in person.get_alternate_names():
            firstnam = self.rem_spaces(name.get_first_name().strip())
            suffix = ""
            surname = self.rem_spaces(name . get_surname())
            suffix = name.get_suffix()
            if firstnam:
                if suffix:
                    alias = "#alias %s_/%s_%s/" % ( firstnam, self.rem_spaces(suffix) , surname )
                else:
                    alias = "#alias %s_/%s/" % ( firstnam, surname )
            else:
                if suffix:
                    alias = "#alias %s_%s_%s" % ( firstname, self.rem_spaces(suffix) , surname )
                else:
                    alias = "#alias %s_%s" % ( firstname, surname )
           
            othername += " " + alias
        title= self.get_title(person)
        if title:
            othername += " " + title
        return ret,othername

    def get_title(self,person):
        title = ""
        for event_ref in person.get_event_ref_list():
            role = int(event_ref.get_role())
            if role != EventRoleType.PRIMARY:
                next
            else:
                event = self.db.get_event_from_handle(event_ref.ref)
                etype = int(event.get_type())
                dateobj  = event.get_date_object()
                if dateobj:
                    date = self.format_date(dateobj)
                if etype ==  EventType.NOB_TITLE:
                    descr = event.get_description()
                    if descr:
                        if dateobj:
                            title += " [:" + self.rem_spaces(descr) + ":" + date + "]"
                        else:
                            title += " [:" + self.rem_spaces(descr) + ":]" 
        return title 
                

    def get_wedding_data(self,family):
        ret = "";
        event_ref_list = family.get_event_ref_list()
        m_date = ""
        m_place = ""
        m_source = ""
        married = 0
        eng_date = ""
        eng_place = ""
        eng_source = ""
        engaged = 0
        div_date = ""
        divorced = 0
        for event_ref in event_ref_list:
            event = self.db.get_event_from_handle(event_ref.ref)
            if event.get_type() == EventType.MARRIAGE:
                married = 1
                m_date = self.format_date( event.get_date_object())
                place_handle = event.get_place_handle()
                if place_handle:
                    m_place = _pd.display_event(self.db, event)
                source = self.get_primary_source( event.get_citation_list())
                if source:
                    m_source=self.get_source_txt(source)

            if event.get_type() == EventType.ENGAGEMENT:
                engaged = 1
                eng_date = self.format_date( event.get_date_object())
                place_handle = event.get_place_handle()
                if place_handle:
                    eng_place = _pd.display_event(self.db, event)
                source = self.get_primary_source( event.get_citation_list())
                if source:
                    eng_source=self.get_source_txt(source)
            if event.get_type() == EventType.DIVORCE:
                divorced = 1
                div_date = self.format_date( event.get_date_object())
        if married == 1:
            if m_date != "":
                ret = ret + m_date
            if m_place != "" and m_source != "":
                ret = ret + " #mp %s #ms %s" % (self.rem_spaces( m_place), self.rem_spaces( m_source))
            if m_place != "" and m_source == "":
                ret = ret + " #mp %s" % self.rem_spaces( m_place)
            if m_source != "" and m_place == "":
                ret = ret + " #ms %s" % self.rem_spaces( m_source)
        elif engaged == 1:
            """Geneweb only supports either Marriage or engagement"""
            if eng_date != "":
                ret = ret + eng_date
            if m_place != "" and m_source != "":
                ret = ret + " #mp %s #ms %s" % (self.rem_spaces( m_place), self.rem_spaces( m_source))
            if eng_place != "" and m_source == "":
                ret = ret + " #mp %s" % self.rem_spaces( m_place)
            if eng_source != "" and m_place == "":
                ret = ret + " #ms %s" % self.rem_spaces( m_source)
        else:
            if family.get_relationship() != FamilyRelType.MARRIED:
                """Not married or engaged"""
                ret = ret + " #nm"

        if divorced == 1:
            if div_date != "":
                ret = ret + " -%s" %div_date
            else:
                ret = ret + " -0"

        return ret

    def get_primary_source(self,reflist):
        ret = ""
        if reflist:
            for handle in reflist:
                citation = self.db.get_citation_from_handle(handle)
                src_handle = citation.get_reference_handle()
                source = self.db.get_source_from_handle(src_handle)
                if source:
                    return source
    
    def format_single_date(self, subdate, cal, mode):
        retval = ""
        (day, month, year, sl) = subdate
        
        cal_type = ""
        if cal == Date.CAL_HEBREW:
            cal_type = "H"
        elif cal == Date.CAL_FRENCH:
            cal_type = "F"
        elif cal == Date.CAL_JULIAN:
            cal_type = "J"
        
        mode_prefix = ""
        if mode == Date.MOD_ABOUT:
            mode_prefix = "~"
        elif mode == Date.MOD_BEFORE:
            mode_prefix = "<"
        elif mode == Date.MOD_AFTER:
            mode_prefix = ">"
            
        if year > 0:
            if month > 0:
                if day > 0:
                    retval = "%s%s/%s/%s%s" % (mode_prefix,day,month,year,cal_type)
                else:
                    retval = "%s%s/%s%s" % (mode_prefix,month,year,cal_type)
            else:
                retval = "%s%s%s" % (mode_prefix,year,cal_type)
        return retval

    
    def format_date(self,date):
        retval = ""
        if date.get_modifier() == Date.MOD_TEXTONLY:
            retval = "0(%s)" % self.rem_spaces(date.get_text())
        elif not date.is_empty():
            mod = date.get_modifier()
            cal = cal = date.get_calendar()
            if mod == Date.MOD_SPAN or mod == Date.MOD_RANGE:
                retval = "%s..%s" % (
                    self.format_single_date(date.get_start_date(), Date.CAL_GREGORIAN,mod),
                    self.format_single_date(date.get_stop_date(),cal,mod))
            else:
                retval = self.format_single_date(date.get_start_date(),cal,mod)
        return retval

#    def iso8859(self,s):
#        return s.encode('iso-8859-1','xmlcharrefreplace')

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def export_data(database, filename, user, option_box=None):
    gw = GeneWebPlusWriter(database, filename, user, option_box)
    return gw.export_data()
