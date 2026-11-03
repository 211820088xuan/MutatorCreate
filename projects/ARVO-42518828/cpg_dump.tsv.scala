
importCpg("/root/gyx/mutator_create/cpg_files/gpac_319d44795db1.cpg")
cpg.method.l.foreach { m =>
  println(s"@@M\t${m.filename}\t${m.name}\t${m.lineNumber.getOrElse(0)}\t${m.lineNumberEnd.getOrElse(0)}\t${if (m.isExternal) 1 else 0}")
}
cpg.call.l.foreach { c =>
  val cs = c.callee.l.map(_.name).distinct.mkString("|")
  if (cs.nonEmpty) {
    val cm = c.method
    println(s"@@C\t${cm.filename}\t${cm.name}\t${cs}")
  }
}
