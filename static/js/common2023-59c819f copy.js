/*  Prototype JavaScript framework, version 1.7.3
 *  (c) 2005-2010 Sam Stephenson
 *  script.aculo.us effects.js v1.7.1_beta3
 *
 *  These libraries are freely distributable under the terms of an MIT-style license.
 *--------------------------------------------------------------------------*/

var Prototype = {
  Version: '1.7.3',
  Browser: (function(){
    var ua = navigator.userAgent;
    var isOpera = Object.prototype.toString.call(window.opera) == '[object Opera]';
    return {
      IE:             !!window.attachEvent && !isOpera,
      Opera:          isOpera,
      WebKit:         ua.indexOf('AppleWebKit/') > -1,
      Gecko:          ua.indexOf('Gecko') > -1 && ua.indexOf('KHTML') === -1,
      MobileSafari:   /Apple.*Mobile/.test(ua)
    }
  })(),

  BrowserFeatures: {
    XPath: !!document.evaluate,
    SelectorsAPI: !!document.querySelector,
    ElementExtensions: (function() {
      var constructor = window.Element || window.HTMLElement;
      return !!(constructor && constructor.prototype);
    })(),
    SpecificElementExtensions: (function() {
      if (typeof window.HTMLDivElement !== 'undefined')
        return true;
      var div = document.createElement('div'),
          form = document.createElement('form'),
          isSupported = false;
      if (div['__proto__'] && (div['__proto__'] !== form['__proto__'])) {
        isSupported = true;
      }
      div = form = null;
      return isSupported;
    })()
  },

  ScriptFragment: '<script[^>]*>([\\S\\s]*?)<\/script\\s*>',
  emptyFunction: function() { },
  K: function(x) { return x }
};

var Class = (function() {
  function subclass() {};
  function create() {
    var parent = null, properties = $A(arguments);
    if (Object.isFunction(properties[0]))
      parent = properties.shift();

    function klass() {
      this.initialize.apply(this, arguments);
    }

    Object.extend(klass, Class.Methods);
    klass.superclass = parent;
    klass.subclasses = [];

    if (parent) {
      subclass.prototype = parent.prototype;
      klass.prototype = new subclass;
      parent.subclasses.push(klass);
    }

    for (var i = 0, length = properties.length; i < length; i++)
      klass.addMethods(properties[i]);

    if (!klass.prototype.initialize)
      klass.prototype.initialize = Prototype.emptyFunction;

    klass.prototype.constructor = klass;
    return klass;
  }

  function addMethods(source) {
    var ancestor   = this.superclass && this.superclass.prototype,
        properties = Object.keys(source);

    for (var i = 0, length = properties.length; i < length; i++) {
      var property = properties[i], value = source[property];
      if (ancestor && Object.isFunction(value) &&
          value.argumentNames()[0] == "$super") {
        var method = value;
        value = (function(m) {
          return function() { return ancestor[m].apply(this, arguments); };
        })(property).wrap(method);
      }
      this.prototype[property] = value;
    }
    return this;
  }

  return {
    create: create,
    Methods: {
      addMethods: addMethods
    }
  };
})();

(function() {
  var _toString = Object.prototype.toString;

  function extend(destination, source) {
    for (var property in source)
      destination[property] = source[property];
    return destination;
  }

  function isElement(object) {
    return !!(object && object.nodeType == 1);
  }

  function isArray(object) {
    return _toString.call(object) === '[object Array]';
  }

  function isFunction(object) {
    return _toString.call(object) === '[object Function]';
  }

  function isString(object) {
    return _toString.call(object) === '[object String]';
  }

  function isUndefined(object) {
    return typeof object === "undefined";
  }

  extend(Object, {
    extend:      extend,
    isElement:   isElement,
    isArray:     isArray,
    isFunction:  isFunction,
    isString:    isString,
    isUndefined: isUndefined
  });
})();

Object.extend(Function.prototype, (function() {
  var slice = Array.prototype.slice;

  function update(array, args) {
    var arrayLength = array.length, length = args.length;
    while (length--) array[arrayLength + length] = args[length];
    return array;
  }

  function merge(array, args) {
    array = slice.call(array, 0);
    return update(array, args);
  }
  
  function argumentNames() {
    var names = this.toString().match(/^[\s\(]*function[^(]*\(([^)]*)\)/)[1]
      .replace(/\s+/g, '').split(',');
    return names.length == 1 && !names[0] ? [] : names;
  }

  function bind(context) {
    if (arguments.length < 2 && Object.isUndefined(arguments[0])) return this;
    var __method = this, args = slice.call(arguments, 1);
    return function() {
      var a = merge(args, arguments);
      return __method.apply(context, a);
    }
  }

  function defer() {
    var args = update([0.01], arguments);
    return this.delay.apply(this, args);
  }

  function wrap(wrapper) {
    var __method = this;
    return function() {
      var a = update([__method.bind(this)], arguments);
      return wrapper.apply(this, a);
    }
  }
  
  function methodize() {
    if (this._methodized) return this._methodized;
    var __method = this;
    return this._methodized = function() {
      var a = update([this], arguments);
      return __method.apply(null, a);
    };
  }

  return {
    argumentNames: argumentNames,
    bind:          bind,
    defer:         defer,
    wrap:          wrap,
    methodize:     methodize
  };
})());

var PeriodicalExecuter = Class.create({
  initialize: function(callback, frequency) {
    this.callback = callback;
    this.frequency = frequency;
    this.currentlyExecuting = false;
    this.registerCallback();
  },
  registerCallback: function() {
    this.timer = setInterval(this.onTimerEvent.bind(this), this.frequency * 1000);
  },
  stop: function() {
    if (!this.timer) return;
    clearInterval(this.timer);
    this.timer = null;
  },
  onTimerEvent: function() {
    if (!this.currentlyExecuting) {
      try {
        this.currentlyExecuting = true;
        this.callback(this);
        this.currentlyExecuting = false;
      } catch(e) {
        this.currentlyExecuting = false;
        throw e;
      }
    }
  }
});

Object.extend(String.prototype, {
  strip: function() {
    return this.replace(/^\s+/, '').replace(/\s+$/, '');
  },
  parseColor: function() {
    var color = '#';
    if (this.slice(0, 4) == 'rgb(') {
      var cols = this.slice(4, this.length - 1).split(',');
      var i = 0; do { color += parseInt(cols[i]).toColorPart() } while (++i < 3);
    } else {
      if (this.slice(0, 1) == '#') {
        if (this.length == 4) for (var i = 1; i < 4; i++) color += (this.charAt(i) + this.charAt(i)).toLowerCase();
        if (this.length == 7) color = this.toLowerCase();
      }
    }
    return (color.length == 7 ? color : (arguments[0] || this));
  }
});

var $break = {};

var Enumerable = {
  each: function(iterator, context) {
    try {
      this._each(iterator, context);
    } catch (e) {
      if (e != $break) throw e;
    }
    return this;
  },
  findAll: function(iterator, context) {
    var results = [];
    this.each(function(value, index) {
      if (iterator.call(context, value, index))
        results.push(value);
    });
    return results;
  },
  
  inject: function(memo, iterator, context) {
    this.each(function(value, index) {
      memo = iterator.call(context, memo, value, index);
    });
    return memo;
  },
  
  pluck: function(property) {
    var results = [];
    this.each(function(value) {
      results.push(value[property]);
    });
    return results;
  },
  
  toArray: function() {
    return this.map();
  },
  
  map: function(iterator, context) {
    iterator = iterator || Prototype.K;
    var results = [];
    this.each(function(value, index) {
      results.push(iterator.call(context, value, index));
    }, this);
    return results;
  }
};

function $A(iterable) {
  if (!iterable) return [];
  if (iterable.toArray) return iterable.toArray();
  var length = iterable.length || 0, results = new Array(length);
  while (length--) results[length] = iterable[length];
  return results;
}

(function() {
  var arrayProto = Array.prototype,
      slice = arrayProto.slice;

  function Last() {
      return this[this.length - 1];
  }
  
  function first() {
    return this[0];
  }

  Object.extend(arrayProto, Enumerable);
  Object.extend(arrayProto, {
    _each: function(iterator) {
      for (var i = 0, length = this.length; i < length; i++)
        iterator(this[i]);
    },
    last: Last,
    first: first
  });
})();

Object.extend(Number.prototype, {
  toColorPart: function() {
    return this.toPaddedString(2, 16);
  },
  toPaddedString: function(length, radix) {
    var string = this.toString(radix || 10);
    return '0'.times(length - string.length) + string;
  }
});

var Effect = {
  _elementDoesNotExistError: {
    name: 'ElementDoesNotExistError',
    message: 'The specified DOM element does not exist, but is required for this effect to operate'
  },
  PAIRS: {
    'slide': ['SlideDown', 'SlideUp'],
    'blind': ['BlindDown', 'BlindUp'],
    'appear': ['Appear', 'Fade']
  }
};

Effect.Transitions = {
  linear: Prototype.K,
  sinoidal: function(pos) {
    return (-Math.cos(pos * Math.PI) / 2) + 0.5;
  }
};

Effect.ScopedQueue = Class.create(Enumerable, {
  initialize: function() {
    this.effects = [];
    this.interval = null;
  },
  _each: function(iterator) {
    this.effects._each(iterator);
  },
  add: function(effect) {
    var timestamp = new Date().getTime();
    var position = (typeof effect.options.queue == 'string') ?
      effect.options.queue : effect.options.queue.position;
    
    switch(position) {
      case 'end':
        timestamp = this.effects.pluck('finishOn').max() || timestamp;
        break;
    }
    
    effect.startOn += timestamp;
    effect.finishOn += timestamp;

    if (!effect.options.queue.limit || (this.effects.length < effect.options.queue.limit))
      this.effects.push(effect);
    
    if (!this.interval)
      this.interval = setInterval(this.loop.bind(this), 15);
  },
  remove: function(effect) {
    this.effects = this.effects.reject(function(e) { return e == effect; });
    if (this.effects.length == 0) {
      clearInterval(this.interval);
      this.interval = null;
    }
  },
  loop: function() {
    var timePos = new Date().getTime();
    for (var i = 0, len = this.effects.length; i < len; i++)
      this.effects[i] && this.effects[i].loop(timePos);
  }
});

Effect.Queues = {
  instances: new Hash(),
  get: function(queueName) {
    if (typeof queueName != 'string') return queueName;
    return this.instances.get(queueName) || this.instances.set(queueName, new Effect.ScopedQueue());
  }
};
Effect.Queue = Effect.Queues.get('global');

Effect.DefaultOptions = {
  transition: Effect.Transitions.sinoidal,
  duration: 1.0,
  fps: 100,
  sync: false,
  from: 0.0,
  to: 1.0,
  delay: 0.0,
  queue: 'parallel'
};

Effect.Base = Class.create({
  position: null,
  start: function(options) {
    this.options = Object.extend(Object.extend({}, Effect.DefaultOptions), options || {});
    this.currentFrame = 0;
    this.state = 'idle';
    this.startOn = this.options.delay * 1000;
    this.finishOn = this.startOn + (this.options.duration * 1000);
    this.fromToDelta = this.options.to - this.options.from;
    this.totalTime = this.finishOn - this.startOn;
    this.totalFrames = this.options.fps * this.options.duration;
    
    this.render = (function(pos) {
      if (this.state === "idle") {
        this.state = "running";
        if (this.setup) this.setup();
      }
      if (this.state === "running") {
        pos = (this.options.transition(pos) * this.fromToDelta) + this.options.from;
        this.position = pos;
        if (this.update) this.update(pos);
      }
    }).bind(this);
    
    if (!this.options.sync)
      Effect.Queues.get(typeof this.options.queue == 'string' ?
        'global' : this.options.queue.scope).add(this);
  },
  loop: function(timePos) {
    if (timePos >= this.startOn) {
      if (timePos >= this.finishOn) {
        this.render(1.0);
        this.cancel();
        if (this.finish) this.finish();
        return;
      }
      var pos = (timePos - this.startOn) / this.totalTime,
        frame = Math.round(pos * this.totalFrames);
      if (frame > this.currentFrame) {
        this.render(pos);
        this.currentFrame = frame;
      }
    }
  },
  cancel: function() {
    if (!this.options.sync)
      Effect.Queues.get(typeof this.options.queue == 'string' ?
        'global' : this.options.queue.scope).remove(this);
    this.state = 'finished';
  }
});

Effect.Scale = Class.create(Effect.Base, {
    initialize: function(element, percent) {
      this.element = $(element);
      if(!this.element) throw(Effect._elementDoesNotExistError);
      var options = Object.extend({
        scaleX: true,
        scaleY: true,
        scaleContent: true,
        scaleFromCenter: false,
        scaleMode: 'box',
        scaleFrom: 100.0,
        scaleTo:   percent
      }, arguments[2] || {});
      this.start(options);
    },
    setup: function() {
      this.elementPositioning = this.element.getStyle('position');
      this.originalTop = this.element.offsetTop;
      this.originalLeft = this.element.offsetLeft;
      
      var sm = this.options.scaleMode;
      var h = (sm == 'box') ? this.element.offsetHeight : this.element.scrollHeight;
      var w = (sm == 'box') ? this.element.offsetWidth : this.element.scrollWidth;
      
      this.dims = [h, w];
      this.factor = (this.options.scaleTo - this.options.scaleFrom) / 100;
    },
    update: function(position) {
      var currentScale = (this.options.scaleFrom / 100.0) + (this.factor * position);
      this.setDimensions(this.dims[0] * currentScale, this.dims[1] * currentScale);
    },
    setDimensions: function(height, width) {
      var d = {};
      if (this.options.scaleX) d.width = Math.round(width) + 'px';
      if (this.options.scaleY) d.height = Math.round(height) + 'px';
      this.element.setStyle(d);
    }
});


Effect.SlideDown = function(element) {
  element = $(element).cleanWhitespace();
  var userOptions = arguments[1] || {};
  var elementDimensions = element.getDimensions();

  var slideOperationState = {
    _temporaryWrapper: null,
    _originalInnerStyle: {}
  };

  var slideCallbacksAndOptions = {
    scaleContent: false,
    scaleX: false,
    scaleFrom: window.opera ? 0 : 1,
    scaleMode: {originalHeight: elementDimensions.height, originalWidth: elementDimensions.width},
    restoreAfterFinish: true,
    slideState: slideOperationState,

    beforeSetupInternal: function(effect) {
      var state = effect.options.slideState;
      var originalFirstChild = effect.element.down();

      if (originalFirstChild) {
          state._originalInnerStyle.position = originalFirstChild.getStyle('position');
          state._originalInnerStyle.bottom = originalFirstChild.getStyle('bottom');
      }
      if (!originalFirstChild) {
        state._temporaryWrapper = new Element('div');
        state._temporaryWrapper.setStyle({ margin: '0px', padding: '0px', border: 'none', display: 'block', overflow: 'hidden' });
        while (effect.element.firstChild) {
          state._temporaryWrapper.appendChild(effect.element.firstChild);
        }
        effect.element.appendChild(state._temporaryWrapper);
      }
    },
    afterSetup: function(effect) {
      effect.element.makePositioned();
      var innerElement = effect.element.down();
      if (innerElement) innerElement.makePositioned();
      if(window.opera) effect.element.setStyle({top: ''});
      effect.element.makeClipping().setStyle({height: '0px'}).show();
    },
    afterUpdateInternal: function(effect) {
      var innerElement = effect.element.down();
      if(innerElement) {
        var currentOuterHeight = effect.element.clientHeight;
        var fullOriginalOuterHeight = effect.options.scaleMode.originalHeight;
        innerElement.setStyle({bottom: (fullOriginalOuterHeight - currentOuterHeight) + 'px' });
      }
    },
    afterFinishInternal: function(effect) {
      var state = effect.options.slideState;
      effect.element.undoClipping().undoPositioned();
      var innerElement = effect.element.down();
      if (innerElement) {
        innerElement.undoPositioned();
        var oiStyle = state._originalInnerStyle;
        if (state._temporaryWrapper && innerElement === state._temporaryWrapper) {
          innerElement.style.bottom = '';
        } else if (!state._temporaryWrapper && innerElement && typeof oiStyle === 'object') {
          innerElement.setStyle({position: oiStyle.position || ''});
          innerElement.setStyle({bottom: oiStyle.bottom || ''});
        } else if (innerElement) {
            innerElement.style.position = '';
            innerElement.style.bottom = '';
        }
      }
      if (state._temporaryWrapper) {
        while (state._temporaryWrapper.firstChild) {
          effect.element.appendChild(state._temporaryWrapper.firstChild);
        }
        effect.element.removeChild(state._temporaryWrapper);
        state._temporaryWrapper = null;
      }
    }
  };
  var allOptions = Object.extend(Object.extend({}, userOptions), slideCallbacksAndOptions);
  return new Effect.Scale(element, 100, allOptions);
};

Effect.SlideUp = function(element) {
  element = $(element).cleanWhitespace();
  var userOptions = arguments[1] || {};
  var elementDimensions = element.getDimensions();

  var slideOperationState = {
    _temporaryWrapper: null,
    _originalInnerStyle: {},
    _originalOuterStyle: {}
  };

  var slideCallbacksAndOptions = {
    scaleContent: false,
    scaleX: false,
    scaleMode: {originalHeight: elementDimensions.height, originalWidth: elementDimensions.width},
    scaleFrom: 100,
    restoreAfterFinish: true,
    slideState: slideOperationState,

    beforeSetupInternal: function(effect) {
        var state = effect.options.slideState;
        var originalFirstChild = effect.element.down();
        if (originalFirstChild) {
            state._originalInnerStyle.position = originalFirstChild.getStyle('position');
            state._originalInnerStyle.bottom = originalFirstChild.getStyle('bottom');
        }
        state._originalOuterStyle.bottom = effect.element.getStyle('bottom');
        if (!originalFirstChild) {
            state._temporaryWrapper = new Element('div');
            state._temporaryWrapper.setStyle({ margin: '0px', padding: '0px', border: 'none', display: 'block', overflow: 'hidden' });
            while (effect.element.firstChild) {
                state._temporaryWrapper.appendChild(effect.element.firstChild);
            }
            effect.element.appendChild(state._temporaryWrapper);
        }
    },
    beforeStartInternal: function(effect) { 
      effect.element.makePositioned();
      var innerElement = effect.element.down();
      if(innerElement) innerElement.makePositioned();
      if(window.opera) effect.element.setStyle({top: ''});
      effect.element.makeClipping().show();
    },
    afterUpdateInternal: function(effect) {
      var innerElement = effect.element.down();
      if(innerElement) {
        var currentOuterHeight = effect.element.clientHeight;
        var fullOriginalOuterHeight = effect.options.scaleMode.originalHeight;
        innerElement.setStyle({bottom: (fullOriginalOuterHeight - currentOuterHeight) + 'px' });
      }
    },
    afterFinishInternal: function(effect) {
      var state = effect.options.slideState;
      effect.element.hide().undoClipping().undoPositioned();

      var ooStyle = state._originalOuterStyle;
      effect.element.setStyle({ bottom: (typeof ooStyle === 'object' && ooStyle.bottom) ? ooStyle.bottom : '' });

      var innerElement = effect.element.down();
      if (innerElement) {
        innerElement.undoPositioned();
        var oiStyle = state._originalInnerStyle;
        if (state._temporaryWrapper && innerElement === state._temporaryWrapper) {
            innerElement.style.bottom = '';
        } else if (!state._temporaryWrapper && innerElement && typeof oiStyle === 'object') {
          innerElement.setStyle({position: oiStyle.position || ''});
          innerElement.setStyle({bottom: oiStyle.bottom || ''});
        } else if (innerElement) {
            innerElement.style.position = '';
            innerElement.style.bottom = '';
        }
      }
      if (state._temporaryWrapper) {
        while (state._temporaryWrapper.firstChild) {
          effect.element.appendChild(state._temporaryWrapper.firstChild);
        }
        effect.element.removeChild(state._temporaryWrapper);
        state._temporaryWrapper = null;
      }
    }
  };

  var allOptions = Object.extend(Object.extend({}, userOptions), slideCallbacksAndOptions);

  return new Effect.Scale(element, window.opera ? 0 : 1, allOptions);
};

Element.addMethods();

function hideBBCodeShowHide(elem) {
	elem.blur();
	var contentElem = $(elem.parentNode).next();
	var options={duration:0.5};
	if (contentElem.getStyle('display') == 'none') {
		new Effect.SlideDown(contentElem,options);
	} else {
		new Effect.SlideUp(contentElem,options);
	}
}