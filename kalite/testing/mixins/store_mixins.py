import datetime 

from kalite.store.models import StoreItem, StoreTransactionLog

class CreateStoreTransactionLogMixin(object):
    DEFAULTS = {
        'item': StoreItem.all().values()[0].storeitem_id,
        'value': -1*StoreItem.all().values()[0].cost,
        'purchased_at': datetime.datetime.now(),
        'context_type': 'unit',
        'context_id': 1,
    }   
    
    @classmethod
    def create_store_transaction_log(cls, **kwargs):
        fields = CreateStoreTransactionLogMixin.DEFAULTS.copy()
        fields['user'] = kwargs.get("user")
        return StoreTransactionLog.objects.create(**fields)

class StoreMixins(CreateStoreTransactionLogMixin):
    '''
    Toplevel class that has all the mixin methods defined above
    '''
    pass

