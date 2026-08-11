// swift-tools-version: 5.9
import PackageDescription

// MTCKit is deliberately UI-free and platform-neutral so it builds and tests
// with the command line tools alone — no Xcode, no simulator. The SwiftUI app
// layers on top of it later; this is the part that has to be correct.
let package = Package(
    name: "MTCKit",
    platforms: [.iOS(.v16), .macOS(.v13)],
    products: [
        .library(name: "MTCKit", targets: ["MTCKit"]),
        .library(name: "AladdinUI", targets: ["AladdinUI"]),
        .executable(name: "mtckit-verify", targets: ["MTCKitVerify"]),
    ],
    targets: [
        .target(name: "MTCKit"),
        // A plain executable rather than an XCTest target: XCTest ships with
        // Xcode, and these checks must be runnable on a machine that has only
        // the command line tools. `swift run mtckit-verify` exits non-zero on
        // failure, so it drops straight into CI later.
        .executableTarget(name: "MTCKitVerify", dependencies: ["MTCKit"]),
        // SwiftUI type-checks against the macOS SDK with command line tools
        // alone, so the screens are verified here long before Xcode exists.
        // Nothing in this target may import UIKit or use iOS-only modifiers.
        .target(name: "AladdinUI", dependencies: ["MTCKit"]),
    ]
)
