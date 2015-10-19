
/*!
 * lm.js
 * Copyright(c) 2013 Madhusudhan Srinivasa <madhums8@gmail.com>
 * MIT Licensed
 */

var debug = true;

/**
 * New database
 *
 * @param {String} name - name of the database
 * @param {Object} options - options
 *
 * Example
 *   var todoapp = new lm('todoapp', {
 *     debug: false
 *   });
 *
 */

function lm (namespace, options) {
  if (!namespace) {
    throw new Error('Please provide a name for the db');
  }

  var _options = {
    debug: true
  };

  this.options = options || _options;
  debug = this.options.debug;

  // create a namespaced object
  db.store(namespace, {});

  this.namespace = namespace;
  this.collections = [];
}

/**
 * Create a collection within the namespace
 *
 * A collection is just an Array within the namespace of db
 *
 * @param {String} name - name of the collection
 * @param {Array} arr - collection of objects
 * @return {Object}
 * @api public
 *
 * Example
 *   var todos = todoapp.create('todos');
 *   // initialize with a list
 *   var todos = todoapp.create('todos', [
 *     {id: 1, name: 'shopping'},
 *     {id: 2, name: 'washing'}
 *   ]);
 */

lm.prototype.create = function(name, arr) {
  if (!name) {
    throw new Error('Please specify a name');
  }

  // set the object
  var ns = db.retrieve(this.namespace);
  ns[name] = arr || [];
  db.store(this.namespace, ns);

  this.collections.push(name);

  return new Collection(name, this.namespace);
};

/**
 * Remove a collection
 *
 * @param {String} name
 * @return {Object}
 * @api public
 *
 * Example
 *   todoapp.remove('todos');
 */

lm.prototype.remove = function(name) {
  if (!name) {
    throw new Error('Please specify a name');
  }

  // remove from the collections list
  var index = this.collections.indexOf(name);

  // if not found, return
  if (index < 0) {
    throw new Error('Collection does not exist')
  }

  this.collections.splice(index, 1);

  // remove from the db
  var ns = db.retrieve(this.namespace);
  delete ns[name];
  db.store(this.namespace, ns);

  return this;
};

/**
 * Get a collection
 *
 * @param {String} name
 * @return {Object}
 * @api public
 *
 * Example
 *   var archived = todoapp.get('archived');
 */

lm.prototype.get = function(name) {
  if (!name) {
    throw new Error('Please specify a name');
  }

  // remove from the collections list
  var index = this.collections.indexOf(name);

  // if not found, return
  if (index < 0) {
    throw new Error('Collection does not exist');
  }

  return new Query(this.namespace, name);
};


/**
 * Collection
 *
 * @param {String} name
 * @param {String} namespace
 * @api public
 */

function Collection (name, namespace) {
  this.name = name;
  this.namespace = namespace;
}

/**
 * Add a record to the collection
 *
 * @param {Object} record
 * @return {Object}
 * @api public
 *
 * Example
 *   var todos = todoapp.create('todos');
 *   todos.add({
 *     { id: 1, name: 'shopping' }
 *   })
 *
 *   // you can also chain them
 *   var archived = todoapp
 *     .create('archived')
 *     .add({ name: 'shopping', tag: 'outside' })
 *     .add({ name: 'eating', tag: 'kitchen' })
 *     .add({ name: 'bathing', tag: 'inside' })
 *     .add({ name: 'cleaning', tag: 'kitchen' })
 */

Collection.prototype.add = function(doc) {
  if (typeof doc !== 'object') {
    throw new Error('Expecting an object but got '+ typeof doc)
  }

  var ns = db.retrieve(this.namespace);
  ns[this.name].push(doc);
  db.store(this.namespace, ns);

  return this;
};


/**
 * Query
 *
 * @param {String} namespace
 * @param {String} name - name of the collection
 * @return {Object}
 * @api public
 */

function Query (namespace, name) {
  this.namespace = namespace;
  this.collectionName = name;
}

/**
 * Find
 *
 * @param {Object} criteria
 * @param {Function} callback - callback function
 * @return {Object}
 * @api public
 *
 * Example
 *   var archived = todoapp.get('archived')
 *   archived.find({ tag: 'kitchen' }, function (err, docs) {
 *     console.log(docs)
 *
 *     docs.find({ name: 'eating' }, function (err, records) {
 *       console.log(records)
 *     })
 *   })
 *
 * Multiple criterias are not supported yet
 */

Query.prototype.find = function(criteria, callback) {
  if (!arguments.length) {
    throw new Error('Please specify a criteria or a callback');
  }

  if (typeof criteria === 'function') {
    // return the whole collection
    callback = criteria;
    criteria = {};
  }

  var ns = db.retrieve(this.namespace);
  var collection = ns[this.collectionName];

  // no criteries given, so return the whole collection
  if (!Object.keys(criteria).length) {
    callback(collection);
  } else {
    var keys = Object.keys(criteria);
    var _docProto = new Document(this.namespace, this.collectionName);

    // filter the collection with the given criterias
    var result = collection.filter(function (doc) {
      // loop over criteria
      for (var i = keys.length - 1; i >= 0; i--) {
        if (doc[keys[i]] === criteria[keys[i]]) {
          // change the prototype of the document to Document
          doc.__proto__ = _docProto;
          return true;
        }
      };
    });

    // change the prototype of result to current instance
    result.__proto__ = this;

    callback(result);
  }

  return this;
};


/**
 * Document constructor
 *
 * @param {Type} name
 * @return {Type}
 * @api public
 */

function Document (namespace, collectionName) {
  this.namespace = namespace;
  this.collectionName = collectionName;
}

/**
 * Update a document
 *
 * @param {Object} obj
 * @return {Object}
 * @api public
 *
 * Example
 *   var archived = todoapp.get('archived')
 *   archived.find({ tag: 'kitchen' }, function (docs) {
 *     var record = docs[0];
 *
 *     record.update({ tag: 'utensils' })
 *   })
 */

Document.prototype.update = function (obj) {
  var doc = this;
  var keys = Object.keys(obj);

  // retrieve the collection from db
  var ns = db.retrieve(this.namespace);
  var collection = ns[this.collectionName];

  // update the document in the collection
  var updated = collection.map(function (d) {
    for (var i = keys.length - 1; i >= 0; i--) {
      if (d[keys[i]] === doc[keys[i]]) {
        d[keys[i]] = obj[keys[i]];

        // update current document
        doc[keys[i]] = obj[keys[i]];
      }
    };
    return d;
  });

  // store the updated collection in the db
  ns[this.collectionName] = updated;
  db.store(this.namespace, ns);

  return doc;
}

/**
 * Remove a document
 *
 * @return {undefined}
 * @api public
 *
 * Example
 *   var archived = todoapp.get('archived')
 *   archived.find({ tag: 'kitchen' }, function (docs) {
 *     var record = docs[0];
 *
 *     record.remove()
 *   })
 */

Document.prototype.remove = function () {
  var doc = this;

  // retrieve the collection from db
  var ns = db.retrieve(this.namespace);
  var collection = ns[this.collectionName];

  // update the document in the collection
  var removed = collection.filter(function (d) {
    // filter the ones that are not equal, hence eleminating the current doc
    return !isEqual(d, doc, [], []);
  });

  // store the updated collection in the db
  ns[this.collectionName] = removed;
  db.store(this.namespace, ns);

  doc = undefined;

  var keys = Object.keys(this);

  // set all the attributes to undefined
  for (var i = keys.length - 1; i >= 0; i--) {
    this[keys[i]] = undefined;
  };

  return doc;
}


var db = {}

/**
 * Alias function for localStorage.setObject
 *
 * @param {String} key - name of the object
 * @param {Object} object - object that needs to be stored
 * @api public
 */

db.store = function (key, object) {
  localStorage.setObject(key, object);
};

/**
 * Alias function for localStorage.getObject
 *
 * @param {String} key - name of the object to retrieve
 * @return {Object}
 * @api public
 */

db.retrieve = function (key) {
  return localStorage.getObject(key);
};

/**
 * Alias function for localStorage.removeObject
 *
 * @param {String} key - name of the object to remove
 * @api public
 */

db.remove = function () {
  localStorage.removeObject(key);
};

/**
 * Check if the given key exists in localStorage
 *
 * @param {String} key - object that needs to be checked for existence
 * @return {Boolean}
 * @api public
 */

db.exists = function (key) {
  var obj = localStorage.getObject(key);
  return !!obj && !!Object.keys(obj).length;
};

/**
 * Clear localstorage
 *
 * @api public
 */

db.clear = function () {
  localStorage.clear();
}


/**
 * Some generic localStorage get and set Object methods
 */

Storage.prototype.setObject = function(key, value) {
  this.setItem(key, JSON.stringify(value));
};

Storage.prototype.getObject = function(key) {
  var value = this.getItem(key);
  var object = value && JSON.parse(value);
  // Firefox fix.
  if (typeof object == 'string') {
    object = object && JSON.parse(object);
  }
  return object;
};

Storage.prototype.removeObject = function (key) {
  this.removeItem(key);
};


/**
 * log to console
 */

function log (message) {
  if (debug) console.log(message);
}

// Taken from underscore.js - http://underscorejs.org/underscore.js
// Internal recursive comparison function for `isEqual`.
function isEqual (a, b, aStack, bStack) {
  // Identical objects are equal. `0 === -0`, but they aren't identical.
  // See the Harmony `egal` proposal: http://wiki.ecmascript.org/doku.php?id=harmony:egal.
  if (a === b) return a !== 0 || 1 / a == 1 / b;
  // A strict comparison is necessary because `null == undefined`.
  if (a == null || b == null) return a === b;
  // Unwrap any wrapped objects.
  // if (a instanceof _) a = a._wrapped;
  // if (b instanceof _) b = b._wrapped;
  // Compare `[[Class]]` names.
  var className = toString.call(a);
  if (className != toString.call(b)) return false;
  switch (className) {
    // Strings, numbers, dates, and booleans are compared by value.
    case '[object String]':
      // Primitives and their corresponding object wrappers are equivalent; thus, `"5"` is
      // equivalent to `new String("5")`.
      return a == String(b);
    case '[object Number]':
      // `NaN`s are equivalent, but non-reflexive. An `egal` comparison is performed for
      // other numeric values.
      return a != +a ? b != +b : (a == 0 ? 1 / a == 1 / b : a == +b);
    case '[object Date]':
    case '[object Boolean]':
      // Coerce dates and booleans to numeric primitive values. Dates are compared by their
      // millisecond representations. Note that invalid dates with millisecond representations
      // of `NaN` are not equivalent.
      return +a == +b;
    // RegExps are compared by their source patterns and flags.
    case '[object RegExp]':
      return a.source == b.source &&
             a.global == b.global &&
             a.multiline == b.multiline &&
             a.ignoreCase == b.ignoreCase;
  }
  if (typeof a != 'object' || typeof b != 'object') return false;
  // Assume equality for cyclic structures. The algorithm for detecting cyclic
  // structures is adapted from ES 5.1 section 15.12.3, abstract operation `JO`.
  var length = aStack.length;
  while (length--) {
    // Linear search. Performance is inversely proportional to the number of
    // unique nested structures.
    if (aStack[length] == a) return bStack[length] == b;
  }
  // Add the first object to the stack of traversed objects.
  aStack.push(a);
  bStack.push(b);
  var size = 0, result = true;
  // Recursively compare objects and arrays.
  if (className == '[object Array]') {
    // Compare array lengths to determine if a deep comparison is necessary.
    size = a.length;
    result = size == b.length;
    if (result) {
      // Deep compare the contents, ignoring non-numeric properties.
      while (size--) {
        if (!(result = eq(a[size], b[size], aStack, bStack))) break;
      }
    }
  } else {
    // Objects with different constructors are not equivalent, but `Object`s
    // from different frames are.
    var aCtor = a.constructor, bCtor = b.constructor;
    if (aCtor !== bCtor && !(typeof aCtor === 'function' && (aCtor instanceof aCtor) &&
                             typeof bCtor === 'function' && (bCtor instanceof bCtor))) {
      // avoid this check
      // return false;
    }
    // Deep compare objects.
    for (var key in a) {
      if (hasOwnProperty.call(a, key)) {
        // Count the expected number of properties.
        size++;
        // Deep compare each member.
        if (!(result = hasOwnProperty.call(b, key) && isEqual(a[key], b[key], aStack, bStack))) break;
      }
    }
    // Ensure that both objects contain the same number of properties.
    if (result) {
      for (key in b) {
        if (hasOwnProperty.call(b, key) && !(size--)) break;
      }
      result = !size;
    }
  }
  // Remove the first object from the stack of traversed objects.
  aStack.pop();
  bStack.pop();
  return result;
};
