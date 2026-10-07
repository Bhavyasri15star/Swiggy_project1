// Express 4 does not forward a rejected promise from an async route handler
// to the error-handling middleware — an unhandled throw inside one hangs
// the request forever (no response is ever sent) and crashes the process
// via an unhandled rejection. Wrapping every async handler with this
// forwards the rejection to next(err), so index.js's error middleware
// actually runs and a response is always sent.
function asyncHandler(fn) {
  return function (req, res, next) {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

module.exports = { asyncHandler };
