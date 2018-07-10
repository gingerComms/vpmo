import { Component, OnInit } from '@angular/core';
import { User } from '../user';
import { AuthenticationService } from '../../_services/authentication.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {

  fullname: string;

  constructor(private authService: AuthenticationService) {}

  ngOnInit() {
    this.authService.currentUser.subscribe(user => this.fullname = user.fullname);
    console.log(this.fullname);
  }

}
