function CountDownTimer(duration, granularity) {
  this.duration = duration
  this.granularity = granularity || 1000
  this.tickFtns = []
  this.running = false
  this.remaining = duration
}

CountDownTimer.prototype.start = function() {
  if (this.running) return

  this.running = true
  let start = Date.now()
  let that = this
  let obj

  (function timer() {
    that.remaining = that.duration - (((Date.now() - start) / 1000) | 0)

    if (that.remaining > 0) {
      setTimeout(timer, that.granularity)
    } else {
      that.remaining = 0
      that.running = false
    }

    obj = CountDownTimer.parse(that.remaining)
    that.tickFtns.forEach(function(ftn) {
      ftn.call(this, obj.minutes, obj.seconds)
    }, that)
  }())
}

CountDownTimer.prototype.onTick = function(ftn) {
  if (typeof ftn === "function") this.tickFtns.push(ftn)
  return this
}

CountDownTimer.prototype.expired = function() {
  return !this.running
}

CountDownTimer.parse = function(seconds) {
  return {
    'minutes': (seconds / 60) | 0,
    'seconds': (seconds % 60) | 0
  }
}