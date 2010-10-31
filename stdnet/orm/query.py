from copy import copy
from itertools import izip

from stdnet.exceptions import *


class svset(object):
    
    def __init__(self, result):
        self.result = result
        
    def __len__(self):
        return 1
    


class QuerySet(object):
    '''Queryset manager'''
    
    def __init__(self, meta, fargs = None, eargs = None, filter_sets = None):
        '''A query set is  initialized with
        
        * *meta* an model instance meta attribute,
        * *fargs* dictionary containing the lookup parameters to include.
        * *eargs* dictionary containing the lookup parameters to exclude.
        '''
        self._meta  = meta
        self.fargs  = fargs
        self.eargs  = eargs
        self.filter_sets = filter_sets
        self.qset   = None
        self._seq   = None
        
    def __repr__(self):
        if self._seq is None:
            s = self.__class__.__name__
            if self.fargs:
                s = '%s.filter(%s)' % (s,self.fargs)
            if self.eargs:
                s = '%s.exclude(%s)' % (s,self.eargs)
            return s
        else:
            return str(self._seq)
    
    def __str__(self):
        return self.__repr__()
    
    def get(self, index):
        return self._unwind()[index]
    __getitem__ = get
    
    def filter(self,**kwargs):
        '''Returns a new ``QuerySet`` containing objects that match the given lookup parameters.'''
        kwargs.update(self.fargs)
        return self.__class__(self._meta,fargs=kwargs,eargs=self.eargs)
    
    def exclude(self,**kwargs):
        '''Returns a new ``QuerySet`` containing objects that do not match the given lookup parameters.'''
        kwargs.update(self.eargs)
        return self.__class__(self._meta,fargs=self.fargs,eargs=kwargs)
    
    #def getid(self, id):
    #    meta = self._meta
    #    return meta.cursor.hash(meta.basekey()).get(id)
    
    def count(self):
        '''Return the number of objects in ``self`` without
fetching objects.'''
        self.buildquery()
        if self.qset == 'all':
            meta = self._meta
            return meta.table().size()
        else:
            return len(self.qset)
        
    def __len__(self):
        return self.count()
    
    def buildquery(self):
        '''Build a queryset'''
        if self.qset is not None:
            return
        meta = self._meta
        unique, fargs = self.aggregate(self.fargs)
        if unique:
            self.qset = svset(meta.cursor.get_object(meta, fargs[0], fargs[1]))
        else:
            if self.eargs:
                unique, eargs = self.aggregate(self.eargs, False)
            else:
                eargs = None
            self.qset = self._meta.cursor.query(meta, fargs, eargs, filter_sets = self.filter_sets)
        
    def aggregate(self, kwargs, filter = True):
        '''Aggregate lookup parameters.'''
        unique  = False
        meta    = self._meta
        fields  = meta.dfields
        result  = {}
        # Loop over 
        for name,value in kwargs.items():
            names = name.split('__')
            N = len(names)
            # simple lookup for example filter(name = 'pippo')
            if N == 1:
                field = fields.get(name,None)
                if not field:
                    raise QuerySetError("Could not filter. Field %s not defined." % name)
                value = field.serialize(value)
                unique = field.unique
            # group lookup filter(name_in ['pippo','luca'])
            elif N == 2 and names[1] == 'in':
                field = meta.fields.get(names[0],None)
                if not field:
                    raise QuerySetError("Could not filter. Field %s not defined." % names[0])
                value = field.hash(value)
            else: 
                # Nested lookup. Not available yet!
                raise NotImplementedError("Nested lookup is not yet available")
                      
            if unique:
                result[name] = value
                if filter:
                    result = name,value
                    unique = True
                    break
                else:
                    result[name] = value   
            elif field.index:
                result[name] = value
            else:
                raise QuerySetError("Field %s is not an index. Cannot query." % name)
        return unique, result
    
    def get(self):
        self.buildquery()
        if len(self.qset) == 1:
            try:
                return self.qset.result
            except:
                id = tuple(self.qset)[0]
                meta = self._meta
                return meta.cursor.hash(meta.basekey()).get(id)
        else:
            raise QuerySetError('Get query yielded non unique results')
        
    def items(self):
        '''Generator of instances in queryset.'''
        self.buildquery()
        meta  = self._meta
        model = meta.make
        ids   = self.qset
        if isinstance(ids,svset):
            yield ids.result
        else:
            hash = meta.table()
            if ids == 'all':
                for id,val in hash.items():
                    yield model(id,val)
            else:
                for id,val in izip(ids,hash.mget(ids)):
                    yield model(id,val)
    
    def __iter__(self):
        if self._seq is None:
            self._seq = list(self.items())
        return self._seq.__iter__()
                
    def _unwind(self):
        if not self._seq:
            self._seq = list(self)
        return self._seq
    
    def delete(self, dlist = None):
        '''Delete all the element in the queryset'''
        T = 0
        for el in self:
            T += el.delete(dlist)
        return T
    

class Manager(object):
    '''Manager for :class:`stdnet.orm.StdModel` models.'''
    def get(self, **kwargs):
        qs = self.filter(**kwargs)
        return qs.get()
    
    def get_or_create(self, **kwargs):
        '''Get an object. If it does not exists, it creates one'''
        try:
            res = self.get(**kwargs)
            created = False
        except ObjectNotFund:
            res = self.model(**kwargs)
            res.save()
            created = True
        return res,created
    
    def filter(self, **kwargs):
        return QuerySet(self._meta, fargs = kwargs)
    
    def exclude(self, **kwargs):
        return QuerySet(self._meta, eargs = kwargs)

    def all(self):
        return self.filter()
    
    
class RelatedManager(Manager):
    '''A :class:`Manager` for handling related :class:`stdnet.orm.StdModels`
to a :class:`stdnet.orm.ForeignKey`.'''
    def __init__(self, model, related, fieldname, obj = None):
        self.model      = model
        self.to         = related
        self.fieldname  = fieldname
        self.obj        = obj
    
    def __str__(self):
        return '%s to %s' % (self.model._meta,self.to._meta)
    
    def __get__(self, instance, instance_type=None):
        return self.__class__(self.model,self.to,self.fieldname,instance)
    
    def _get_field(self):
        return self.model._meta.dfields[self.fieldname]
    field = property(_get_field)
    
    def get_related_object(self, id):
        return self.model.objects.get(id = id)
        
    def filter(self, **kwargs):
        if self.obj:
            kwargs[self.fieldname] = self.obj
            return QuerySet(self.to._meta, kwargs)
        else:
            raise QuerySetError('Related manager has no object')
            

class M2MRelatedManager(Manager):
    '''A :class:`RelatedManager` for a :class:`stdnet.orm.ManyToManyField`'''
    def __init__(self, instance, to, st, to_name):
        self.instance = instance
        self.to = to
        self.st = st
        self.to_name = to_name
    
    def add(self, value):
        '''Add *value*, an instance of self.to'''
        if not isinstance(value,self.to):
            raise FieldValueError('%s is not an instance of %s' % (value,self.to._meta))
        if value is self.instance:
            return
        related = getattr(value,self.to_name)
        self._add(value)
        related._add(self.instance)
        
    def _add(self, value):
        self.st.add(value)
        
    def filter(self, **kwargs):
        extrasets = [self.st.id]
        return QuerySet(self.to._meta, kwargs, filter_sets = extrasets)
    

class UnregisteredManager(object):
    
    def __init__(self, model):
        self.model = model
        
    def __getattr__(self, name):
        raise ModelNotRegistered('Model %s is not registered with a backend' % self.model.__name__)


    