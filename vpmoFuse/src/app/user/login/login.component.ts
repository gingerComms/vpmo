import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthenticationService, AlertService } from '../../_services/index';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
  // moduleId: module.id,
})
export class LoginComponent implements OnInit {
  model: any = {};
  loading = false;
  returnUrl: string;
  currentUser: any = {};
  @Output() userLoggedIn = new EventEmitter();


  constructor(
      private route: ActivatedRoute,
      private router: Router,
      private authenticationService: AuthenticationService,
      private alertService: AlertService,
      ) { }

  ngOnInit() {
      // reset login status
      this.authenticationService.logout();

      // get return url from route parameters or default to '/'
      this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/';
      // this.currentUser = this.authenticationService.currentUser.subscribe(currentUser => this.currentUser);
  }

  login() {
      this.loading = true;
      this.authenticationService.login(this.model.email, this.model.password)
          .subscribe(
              data => {
                console.log(this.model.email);
                console.log(localStorage.getItem('currentUser'));
                // this.userLoggedIn.emit(this.model.fullname);
                this.router.navigate(['/user/dashboard']);
              },
              error => {
                this.alertService.error(error);
                this.loading = false;
              });
  }
}
