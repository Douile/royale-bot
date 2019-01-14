import sys

def utils_dispatcher():
    print('Running dispatcher test...')
    import asyncio
    from utils import dispatcher
    def test_a():
        print('This event occurs every minute')
    @asyncio.coroutine
    def test_b():
        print('This event occurs every 2 minutes and is a coroutine')
    loop = asyncio.get_event_loop()
    dis = dispatcher.Dispatcher()
    dis.register(test_a,hours=None,minutes=None)
    dis.register(test_b,hours=None,minutes=list(range(0,60,2)))
    loop.run_until_complete(dis.run())

TESTS = {
    'utils': {
        'dispatcher': utils_dispatcher
    }
}

def recurse_test(tests,args,n=0):
    if n > len(tests):
        print('Test [{0}] not found, [{1}] available at highest level.'.format(' '.join(args),' '.format(tests)))
    else:
        t = tests.get(args[n],None)
        if callable(t):
            t()
        elif isinstance(t,dict):
            recurse_test(t,args,n+1)
        else:
            print('Test [{0}] not found.'.format(' '.join(args)))

if __name__ == '__main__':
    print('Welcome to RoyaleBot code testing facility...\n')
    recurse_test(TESTS,sys.argv[1:][:])
